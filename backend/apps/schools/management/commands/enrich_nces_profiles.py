import csv
from pathlib import Path
from typing import Dict, Iterable

from django.core.management.base import BaseCommand

from apps.schools.models import School
from apps.schools.nces import (
    NCES_DEFAULT_OUT_FIELDS,
    NCES_LAYER_URL,
    choose_school_match,
    clean_state,
    fetch_nces_layer_fields,
    fetch_nces_records,
    normalize_name,
)


PROFILE_FIELD_CANDIDATES = (
    'CONTROL,CONTROL_DESC,SECTOR,SECTOR_DESC,LEVEL,LEVEL_DESC,ICLEVEL,LOCALE,LOCALE_DESC,'
    'ULOCAL,ENROLLMENT,TOTAL_ENROLLMENT,EFYTOTLT,UGDS,GRAD_RATE,C150_4,GRADRATE,'
    'ADM_RATE,ACCEPTANCE_RATE'
)

LOCALE_CODE_MAP = {
    '11': 'City: Large',
    '12': 'City: Midsize',
    '13': 'City: Small',
    '21': 'Suburb: Large',
    '22': 'Suburb: Midsize',
    '23': 'Suburb: Small',
    '31': 'Town: Fringe',
    '32': 'Town: Distant',
    '33': 'Town: Remote',
    '41': 'Rural: Fringe',
    '42': 'Rural: Distant',
    '43': 'Rural: Remote',
}


def _trim(value) -> str:
    return str(value or '').strip()


def _normalize_field_map(record: Dict) -> Dict[str, object]:
    return {str(key).strip().upper(): value for key, value in record.items()}


def _first_value(record_upper: Dict[str, object], keys: Iterable[str]) -> str:
    for key in keys:
        value = _trim(record_upper.get(key.upper()))
        if value:
            return value
    return ''


def _format_integerish(value: str) -> str:
    if not value:
        return ''
    parsed = None
    try:
        parsed = float(value)
    except ValueError:
        return value
    if parsed < 0:
        return ''
    return f'{int(round(parsed)):,}'


def _format_percent(value: str) -> str:
    if not value:
        return ''
    parsed = None
    try:
        parsed = float(value)
    except ValueError:
        return value
    if parsed < 0:
        return ''
    if parsed <= 1:
        parsed *= 100
    return f'{parsed:.1f}%'


def _map_institution_control(value: str) -> str:
    text = _trim(value).lower()
    if not text:
        return School.InstitutionControl.UNKNOWN

    if text in {'1', 'public'} or 'public' in text:
        return School.InstitutionControl.PUBLIC
    if text in {'2'} or 'nonprofit' in text or 'non-profit' in text or 'not-for-profit' in text:
        return School.InstitutionControl.PRIVATE_NONPROFIT
    if text in {'3'} or 'for-profit' in text or 'for profit' in text:
        return School.InstitutionControl.PRIVATE_FOR_PROFIT
    return School.InstitutionControl.UNKNOWN


def _map_institution_level(value: str) -> str:
    text = _trim(value).lower()
    if not text:
        return School.InstitutionLevel.UNKNOWN

    if text in {'4', '4-year', 'four-year'} or '4-year' in text:
        return School.InstitutionLevel.FOUR_YEAR
    if text in {'2', '2-year', 'two-year'} or '2-year' in text:
        return School.InstitutionLevel.TWO_YEAR
    if text in {'1'} or 'less than 2-year' in text:
        return School.InstitutionLevel.LESS_THAN_TWO_YEAR
    return School.InstitutionLevel.UNKNOWN


def _map_locale(value: str) -> str:
    text = _trim(value)
    if not text:
        return ''
    return LOCALE_CODE_MAP.get(text, text)


class Command(BaseCommand):
    help = 'Enrich school profile fields from NCES ArcGIS using unitid/name-state matching.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=0)
        parser.add_argument('--page-size', type=int, default=1000)
        parser.add_argument('--sleep', type=float, default=0.2)
        parser.add_argument('--min-score', type=float, default=0.86)
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--force', action='store_true')
        parser.add_argument('--report', type=str, default='')
        parser.add_argument('--layer-url', type=str, default=NCES_LAYER_URL)
        parser.add_argument('--out-fields', type=str, default='')
        parser.add_argument(
            '--list-fields',
            action='store_true',
            help='Print all available field names from the NCES layer and exit.',
        )

    def handle(self, *args, **options):
        limit = options['limit']
        page_size = options['page_size']
        sleep_seconds = options['sleep']
        min_score = options['min_score']
        dry_run = options['dry_run']
        force = options['force']
        report_path = options['report']
        layer_url = options['layer_url']

        if options['list_fields']:
            fields = fetch_nces_layer_fields(base_url=layer_url)
            for field in fields:
                self.stdout.write(
                    f"{field.get('name', '')}\t{field.get('alias', '')}\t{field.get('type', '')}"
                )
            return

        out_fields = options['out_fields'].strip()
        required_fields = NCES_DEFAULT_OUT_FIELDS.split(',')
        available_field_names = {
            _trim(field.get('name')).upper()
            for field in fetch_nces_layer_fields(base_url=layer_url)
            if _trim(field.get('name'))
        }

        def keep_known_fields(field_names):
            kept = []
            for name in field_names:
                normalized = _trim(name).upper()
                if normalized and normalized in available_field_names and normalized not in kept:
                    kept.append(normalized)
            return kept

        if out_fields:
            requested_parts = [field.strip() for field in out_fields.split(',') if field.strip()]
            for required in required_fields:
                if required not in requested_parts:
                    requested_parts.append(required)
            requested_fields = ','.join(keep_known_fields(requested_parts))
        else:
            default_requested = [field.strip() for field in f'{NCES_DEFAULT_OUT_FIELDS},{PROFILE_FIELD_CANDIDATES}'.split(',')]
            requested_fields = ','.join(keep_known_fields(default_requested))

        schools = list(School.objects.all())
        schools_by_unitid = {}
        schools_by_state_norm = {}
        schools_by_norm = {}
        schools_by_state = {}

        for school in schools:
            if school.nces_unitid:
                schools_by_unitid[school.nces_unitid.strip()] = school

            norm_name = normalize_name(school.name)
            state = clean_state(school.state)
            schools_by_state_norm.setdefault((state, norm_name), []).append(school)
            schools_by_norm.setdefault(norm_name, []).append(school)
            schools_by_state.setdefault(state, []).append(school)

        processed = 0
        matched = 0
        updated = 0
        skipped = 0
        unmatched = 0
        report_rows = []

        for record in fetch_nces_records(
            base_url=layer_url,
            page_size=page_size,
            sleep_seconds=sleep_seconds,
            out_fields=requested_fields,
        ):
            if limit and processed >= limit:
                break
            processed += 1

            school, score, method = choose_school_match(
                nces_record=record,
                schools_by_unitid=schools_by_unitid,
                schools_by_state_norm=schools_by_state_norm,
                schools_by_norm=schools_by_norm,
                schools_by_state=schools_by_state,
                schools_all=schools,
            )

            unitid = _trim(record.get('UNITID'))
            nces_name = _trim(record.get('NAME'))

            if school is None or score < min_score:
                unmatched += 1
                report_rows.append(
                    {
                        'status': 'unmatched',
                        'score': f'{score:.3f}',
                        'method': method,
                        'nces_unitid': unitid,
                        'nces_name': nces_name,
                        'school_id': '',
                        'school_name': '',
                    }
                )
                continue

            matched += 1
            attrs = _normalize_field_map(record)
            control_raw = _first_value(attrs, ('CONTROL_DESC', 'SECTOR_DESC', 'CONTROL', 'SECTOR'))
            level_raw = _first_value(attrs, ('LEVEL_DESC', 'ICLEVEL', 'LEVEL'))
            locale_raw = _first_value(attrs, ('LOCALE_DESC', 'ULOCAL', 'LOCALE'))
            enrollment_raw = _first_value(attrs, ('ENROLLMENT', 'TOTAL_ENROLLMENT', 'EFYTOTLT', 'UGDS'))
            grad_rate_raw = _first_value(attrs, ('GRAD_RATE', 'C150_4', 'GRADRATE'))
            acceptance_rate_raw = _first_value(attrs, ('ADM_RATE', 'ACCEPTANCE_RATE'))
            schoolyear = _first_value(attrs, ('SCHOOLYEAR',))

            new_control = _map_institution_control(control_raw)
            new_level = _map_institution_level(level_raw)
            new_locale = _map_locale(locale_raw)
            new_enrollment = _format_integerish(enrollment_raw)
            new_grad_rate = _format_percent(grad_rate_raw)
            new_acceptance_rate = _format_percent(acceptance_rate_raw)

            change_map = {
                'institution_control': new_control,
                'institution_level': new_level,
                'locale': new_locale,
                'enrollment': new_enrollment,
                'graduation_rate': new_grad_rate,
                'acceptance_rate': new_acceptance_rate,
                'nces_unitid': unitid,
                'nces_name': nces_name,
                'nces_schoolyear': schoolyear,
            }

            update_fields = []
            for field_name, new_value in change_map.items():
                current_value = getattr(school, field_name)
                if force:
                    setattr(school, field_name, new_value)
                    if current_value != new_value:
                        update_fields.append(field_name)
                elif not current_value and new_value:
                    setattr(school, field_name, new_value)
                    update_fields.append(field_name)

            if not update_fields:
                skipped += 1
                report_rows.append(
                    {
                        'status': 'skipped',
                        'score': f'{score:.3f}',
                        'method': method,
                        'nces_unitid': unitid,
                        'nces_name': nces_name,
                        'school_id': school.id,
                        'school_name': school.name,
                    }
                )
                continue

            if not dry_run:
                school.save(update_fields=update_fields)
                if unitid:
                    schools_by_unitid[unitid] = school

            updated += 1
            report_rows.append(
                {
                    'status': 'updated',
                    'score': f'{score:.3f}',
                    'method': method,
                    'nces_unitid': unitid,
                    'nces_name': nces_name,
                    'school_id': school.id,
                    'school_name': school.name,
                }
            )

        if report_path:
            report_file = Path(report_path)
            report_file.parent.mkdir(parents=True, exist_ok=True)
            with report_file.open('w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(
                    csvfile,
                    fieldnames=['status', 'score', 'method', 'nces_unitid', 'nces_name', 'school_id', 'school_name'],
                )
                writer.writeheader()
                writer.writerows(report_rows)
            self.stdout.write(f'Report written: {report_file}')

        self.stdout.write(
            self.style.SUCCESS(
                'Processed={} matched={} updated={} skipped={} unmatched={} dry_run={} fields={}'.format(
                    processed,
                    matched,
                    updated,
                    skipped,
                    unmatched,
                    dry_run,
                    requested_fields,
                )
            )
        )
