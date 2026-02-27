import csv
import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.schools.models import School


DISCIPLINE_KEYWORDS = {
    'road': ('road', 'criterium', 'crit', 'time trial', 'tt'),
    'mtb': ('mountain bike', 'mountain biking', 'mtb'),
    'mtb_xc': ('xc', 'cross-country', 'cross country'),
    'mtb_st': ('short track', 'xcc', 'mtb st'),
    'mtb_enduro': ('enduro',),
    'mtb_downhill': ('downhill', 'dh '),
    'mtb_slalom': ('slalom',),
    'cyclocross': ('cyclocross', 'cross race', 'cx '),
    'track': ('track cycling', 'velodrome'),
}

BOOL_FIELDS = ('road', 'mtb', 'mtb_xc', 'mtb_st', 'mtb_enduro', 'mtb_downhill', 'mtb_slalom', 'cyclocross', 'track')
STATUS_VALUES = {'active', 'inactive', 'unknown', 'limited'}
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def parse_bool(value: str):
    text = (value or '').strip().lower()
    if text in {'1', 'true', 'yes', 'y'}:
        return True
    if text in {'0', 'false', 'no', 'n'}:
        return False
    return None


def infer_disciplines(text: str):
    hay = f' {text.lower()} '
    inferred = {}
    for field, keywords in DISCIPLINE_KEYWORDS.items():
        inferred[field] = any(keyword in hay for keyword in keywords)
    return inferred


class Command(BaseCommand):
    help = 'Apply researched CSEP CSV values to School records.'

    def add_arguments(self, parser):
        parser.add_argument('--input', type=str, required=True)
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--force', action='store_true', help='Allow explicit false overwrites for discipline booleans.')
        parser.add_argument(
            '--no-infer',
            action='store_true',
            help='Only apply explicit discipline booleans from CSV (skip keyword inference from evidence text).',
        )
        parser.add_argument('--report', type=str, default='')

    def handle(self, *args, **options):
        input_path = Path(options['input'])
        if not input_path.exists():
            raise CommandError(f'Input file not found: {input_path}')

        dry_run = options['dry_run']
        force = options['force']
        no_infer = options['no_infer']
        report_path = Path(options['report']) if options['report'] else None

        processed = updated = skipped = failed = 0
        report_rows = []

        with input_path.open('r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                processed += 1
                school = None
                try:
                    school_id = (row.get('school_id') or '').strip()
                    nces = (row.get('nces_unitid') or '').strip()
                    if school_id:
                        school = School.objects.filter(id=int(school_id)).first()
                    if not school and nces:
                        school = School.objects.filter(nces_unitid=nces).first()
                    if not school:
                        failed += 1
                        report_rows.append({'status': 'failed', 'school_id': school_id, 'school_name': row.get('school_name', ''), 'details': 'School not found'})
                        continue

                    changes = []
                    evidence_text = ' '.join(
                        filter(
                            None,
                            [
                                row.get('discipline_evidence_text', ''),
                                row.get('evidence_snippet', ''),
                                row.get('notes', ''),
                            ],
                        )
                    )
                    inferred = {} if no_infer else infer_disciplines(evidence_text)

                    for field in BOOL_FIELDS:
                        explicit = parse_bool(row.get(field, ''))
                        value = explicit if explicit is not None else (True if inferred.get(field) else None)
                        if value is None:
                            continue
                        current = getattr(school, field)
                        if value is True and current is not True:
                            setattr(school, field, True)
                            changes.append(field)
                        elif value is False and force and current is not False:
                            setattr(school, field, False)
                            changes.append(field)

                    # MTB aggregate flag should follow any positive MTB subtype evidence.
                    if any(
                        getattr(school, key)
                        for key in ('mtb', 'mtb_xc', 'mtb_st', 'mtb_enduro', 'mtb_downhill', 'mtb_slalom')
                    ) and school.mtb is not True:
                        school.mtb = True
                        changes.append('mtb')

                    status = (row.get('cycling_program_status') or '').strip().lower()
                    if status in STATUS_VALUES and school.cycling_program_status != status:
                        school.cycling_program_status = status
                        changes.append('cycling_program_status')

                    head_coach = (row.get('head_coach') or '').strip()
                    if head_coach and school.head_coach != head_coach:
                        school.head_coach = head_coach
                        changes.append('head_coach')

                    contact_email = (row.get('contact_email') or '').strip()
                    if contact_email:
                        if EMAIL_RE.match(contact_email):
                            if school.contact_email != contact_email:
                                school.contact_email = contact_email
                                changes.append('contact_email')
                        else:
                            report_rows.append({'status': 'warning', 'school_id': school.id, 'school_name': school.name, 'details': f'Invalid email skipped: {contact_email}'})

                    if changes:
                        updated += 1
                        if not dry_run:
                            school.save(update_fields=sorted(set(changes)))
                        report_rows.append({'status': 'updated', 'school_id': school.id, 'school_name': school.name, 'details': ','.join(sorted(set(changes)))})
                    else:
                        skipped += 1
                        report_rows.append({'status': 'skipped', 'school_id': school.id, 'school_name': school.name, 'details': ''})
                except Exception as exc:  # noqa: BLE001
                    failed += 1
                    report_rows.append({'status': 'failed', 'school_id': row.get('school_id', ''), 'school_name': row.get('school_name', ''), 'details': str(exc)})

        if report_path:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with report_path.open('w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['status', 'school_id', 'school_name', 'details'])
                writer.writeheader()
                writer.writerows(report_rows)
            self.stdout.write(f'Report written: {report_path}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Processed={processed} updated={updated} skipped={skipped} failed={failed} dry_run={dry_run}'
            )
        )
