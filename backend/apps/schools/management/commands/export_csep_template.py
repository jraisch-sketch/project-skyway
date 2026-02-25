import csv
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.schools.models import School


class Command(BaseCommand):
    help = 'Export a CSEP research template CSV from School records.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=0)
        parser.add_argument('--out', type=str, required=True)
        parser.add_argument('--only-missing', action='store_true', help='Only export schools with missing CSEP fields.')
        parser.add_argument('--start-after-id', type=int, default=0, help='Only export schools with id greater than this value.')

    def handle(self, *args, **options):
        limit = options['limit']
        out_path = Path(options['out'])
        only_missing = options['only_missing']
        start_after_id = options['start_after_id']

        qs = School.objects.all().order_by('id')
        if start_after_id:
            qs = qs.filter(id__gt=start_after_id)
        if only_missing:
            qs = qs.filter(
                head_coach=''  # quick practical filter to prioritize incomplete rows
            )

        rows = list(qs[:limit] if limit else qs)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    'school_id',
                    'nces_unitid',
                    'school_name',
                    'school_website',
                    'cycling_website',
                    'research_status',
                    'evidence_url',
                    'evidence_date',
                    'evidence_snippet',
                    'discipline_evidence_text',
                    'road',
                    'mtb_xc',
                    'mtb_st',
                    'mtb_enduro',
                    'mtb_downhill',
                    'mtb_slalom',
                    'cyclocross',
                    'track',
                    'cycling_program_status',
                    'head_coach',
                    'contact_email',
                    'researcher',
                    'notes',
                ],
            )
            writer.writeheader()
            for school in rows:
                writer.writerow(
                    {
                        'school_id': school.id,
                        'nces_unitid': school.nces_unitid,
                        'school_name': school.name,
                        'school_website': school.school_website,
                        'cycling_website': school.cycling_website,
                        'research_status': '',
                        'evidence_url': '',
                        'evidence_date': '',
                        'evidence_snippet': '',
                        'discipline_evidence_text': '',
                        'road': '',
                        'mtb_xc': '',
                        'mtb_st': '',
                        'mtb_enduro': '',
                        'mtb_downhill': '',
                        'mtb_slalom': '',
                        'cyclocross': '',
                        'track': '',
                        'cycling_program_status': '',
                        'head_coach': school.head_coach,
                        'contact_email': school.contact_email,
                        'researcher': '',
                        'notes': '',
                    }
                )

        self.stdout.write(self.style.SUCCESS(f'Exported {len(rows)} rows to {out_path}'))
