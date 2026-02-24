import csv
import os
import time
from pathlib import Path
from typing import Iterable

from django.core.management.base import BaseCommand, CommandError

from apps.schools.models import School
from apps.schools.scorecard import SCORECARD_API_URL, SCORECARD_DEFAULT_FIELDS, fetch_scorecard_school

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


def _extract(record: dict, path: str):
    if path in record and record[path] is not None:
        return record[path]
    current = record
    for segment in path.split('.'):
        if not isinstance(current, dict) or segment not in current:
            return None
        current = current[segment]
    return current


def _first_value(record: dict, paths: Iterable[str]) -> str:
    for path in paths:
        value = _extract(record, path)
        if value is None:
            continue
        text = _trim(value)
        if text:
            return text
    return ''


def _format_integerish(value: str) -> str:
    if not value:
        return ''
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
    if text in {'2'} or 'nonprofit' in text or 'non-profit' in text:
        return School.InstitutionControl.PRIVATE_NONPROFIT
    if text in {'3'} or 'for-profit' in text or 'for profit' in text:
        return School.InstitutionControl.PRIVATE_FOR_PROFIT
    return School.InstitutionControl.UNKNOWN


def _map_institution_level(value: str) -> str:
    text = _trim(value).lower()
    if not text:
        return School.InstitutionLevel.UNKNOWN
    if text in {'3', '4'}:
        return School.InstitutionLevel.FOUR_YEAR
    if text in {'2'}:
        return School.InstitutionLevel.TWO_YEAR
    if text in {'1'}:
        return School.InstitutionLevel.LESS_THAN_TWO_YEAR
    if '4-year' in text:
        return School.InstitutionLevel.FOUR_YEAR
    if '2-year' in text:
        return School.InstitutionLevel.TWO_YEAR
    if 'less than' in text:
        return School.InstitutionLevel.LESS_THAN_TWO_YEAR
    return School.InstitutionLevel.UNKNOWN


def _map_locale(value: str) -> str:
    text = _trim(value)
    if not text:
        return ''
    return LOCALE_CODE_MAP.get(text, text)


class Command(BaseCommand):
    help = 'Enrich school profile fields from College Scorecard using NCES UNITID.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=0)
        parser.add_argument('--sleep', type=float, default=0.1)
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--force', action='store_true')
        parser.add_argument('--report', type=str, default='')
        parser.add_argument('--base-url', type=str, default=SCORECARD_API_URL)
        parser.add_argument('--fields', type=str, default=SCORECARD_DEFAULT_FIELDS)
        parser.add_argument('--api-key', type=str, default='')
        parser.add_argument(
            '--max-rate-limit-failures',
            type=int,
            default=20,
            help='Abort early after this many consecutive HTTP 429 failures.',
        )

    def handle(self, *args, **options):
        limit = options['limit']
        sleep_seconds = options['sleep']
        dry_run = options['dry_run']
        force = options['force']
        report_path = options['report']
        base_url = options['base_url']
        fields = options['fields']
        max_rate_limit_failures = options['max_rate_limit_failures']

        api_key = options['api_key'].strip() or os.getenv('COLLEGE_SCORECARD_API_KEY', '').strip() or 'DEMO_KEY'
        if not api_key:
            raise CommandError('Missing API key. Set COLLEGE_SCORECARD_API_KEY or pass --api-key.')

        queryset = School.objects.exclude(nces_unitid='')
        schools = list(queryset.order_by('id'))

        processed = 0
        updated = 0
        skipped = 0
        unmatched = 0
        failed = 0
        consecutive_rate_limited = 0
        report_rows = []

        for school in schools:
            if limit and processed >= limit:
                break
            processed += 1

            try:
                record = fetch_scorecard_school(
                    unitid=school.nces_unitid,
                    api_key=api_key,
                    base_url=base_url,
                    fields=fields,
                )
            except Exception as exc:  # noqa: BLE001
                failed += 1
                error_text = str(exc)
                if 'HTTP Error 429' in error_text:
                    consecutive_rate_limited += 1
                else:
                    consecutive_rate_limited = 0
                report_rows.append(
                    {
                        'status': 'failed',
                        'nces_unitid': school.nces_unitid,
                        'school_id': school.id,
                        'school_name': school.name,
                        'details': str(exc),
                    }
                )
                if max_rate_limit_failures and consecutive_rate_limited >= max_rate_limit_failures:
                    self.stdout.write(
                        self.style.WARNING(
                            'Aborting early due to repeated 429 rate-limit responses. '
                            'Set COLLEGE_SCORECARD_API_KEY to continue at scale.'
                        )
                    )
                    break
                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)
                continue
            consecutive_rate_limited = 0

            if not record:
                unmatched += 1
                report_rows.append(
                    {
                        'status': 'unmatched',
                        'nces_unitid': school.nces_unitid,
                        'school_id': school.id,
                        'school_name': school.name,
                        'details': '',
                    }
                )
                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)
                continue

            control_raw = _first_value(record, ('school.ownership',))
            level_raw = _first_value(record, ('school.degrees_awarded.predominant',))
            locale_raw = _first_value(record, ('school.locale',))
            enrollment_raw = _first_value(record, ('latest.student.size',))
            acceptance_rate_raw = _first_value(record, ('latest.admissions.admission_rate.overall',))
            grad_rate_raw = _first_value(
                record,
                (
                    'latest.completion.rate_4yr_150nt',
                    'latest.completion.rate_150nt_4yr',
                    'latest.completion.completion_rate_4yr_150nt',
                ),
            )

            new_control = _map_institution_control(control_raw)
            new_level = _map_institution_level(level_raw)
            new_locale = _map_locale(locale_raw)
            new_enrollment = _format_integerish(enrollment_raw)
            new_acceptance_rate = _format_percent(acceptance_rate_raw)
            new_grad_rate = _format_percent(grad_rate_raw)

            change_map = {
                'institution_control': new_control,
                'institution_level': new_level,
                'locale': new_locale,
                'enrollment': new_enrollment,
                'acceptance_rate': new_acceptance_rate,
                'graduation_rate': new_grad_rate,
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
                        'nces_unitid': school.nces_unitid,
                        'school_id': school.id,
                        'school_name': school.name,
                        'details': '',
                    }
                )
            else:
                if not dry_run:
                    school.save(update_fields=update_fields)
                updated += 1
                report_rows.append(
                    {
                        'status': 'updated',
                        'nces_unitid': school.nces_unitid,
                        'school_id': school.id,
                        'school_name': school.name,
                        'details': ','.join(update_fields),
                    }
                )

            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

        if report_path:
            report_file = Path(report_path)
            report_file.parent.mkdir(parents=True, exist_ok=True)
            with report_file.open('w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(
                    csvfile,
                    fieldnames=['status', 'nces_unitid', 'school_id', 'school_name', 'details'],
                )
                writer.writeheader()
                writer.writerows(report_rows)
            self.stdout.write(f'Report written: {report_file}')

        self.stdout.write(
            self.style.SUCCESS(
                'Processed={} updated={} skipped={} unmatched={} failed={} dry_run={}'.format(
                    processed,
                    updated,
                    skipped,
                    unmatched,
                    failed,
                    dry_run,
                )
            )
        )
