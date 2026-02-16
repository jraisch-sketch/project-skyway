import csv
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.schools.models import School
from apps.schools.nces import (
    NCES_LAYER_URL,
    choose_school_match,
    clean_state,
    clean_zip,
    fetch_nces_records,
    full_address,
    normalize_name,
)


class Command(BaseCommand):
    help = 'Import addresses and coordinates from NCES ArcGIS (IPEDS 2022-23 layer).'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=0)
        parser.add_argument('--page-size', type=int, default=1000)
        parser.add_argument('--sleep', type=float, default=0.2)
        parser.add_argument('--min-score', type=float, default=0.86)
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--force', action='store_true')
        parser.add_argument('--report', type=str, default='')
        parser.add_argument('--layer-url', type=str, default=NCES_LAYER_URL)

    def handle(self, *args, **options):
        limit = options['limit']
        page_size = options['page_size']
        sleep_seconds = options['sleep']
        min_score = options['min_score']
        dry_run = options['dry_run']
        force = options['force']
        report_path = options['report']
        layer_url = options['layer_url']

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

        matched = 0
        updated = 0
        skipped = 0
        review = 0
        unmatched = 0
        processed = 0
        report_rows = []

        for record in fetch_nces_records(base_url=layer_url, page_size=page_size, sleep_seconds=sleep_seconds):
            processed += 1
            if limit and processed > limit:
                break

            school, score, method = choose_school_match(
                nces_record=record,
                schools_by_unitid=schools_by_unitid,
                schools_by_state_norm=schools_by_state_norm,
                schools_by_norm=schools_by_norm,
                schools_by_state=schools_by_state,
                schools_all=schools,
            )

            unitid = str(record.get('UNITID') or '').strip()
            name = str(record.get('NAME') or '').strip()
            street = str(record.get('STREET') or '').strip()
            city = str(record.get('CITY') or '').strip()
            state = clean_state(str(record.get('STATE') or ''))
            zip_code = clean_zip(str(record.get('ZIP') or ''))
            lat = record.get('LAT')
            lon = record.get('LON')
            schoolyear = str(record.get('SCHOOLYEAR') or '').strip()

            if school is None or score < min_score:
                unmatched += 1
                report_rows.append(
                    {
                        'status': 'unmatched',
                        'score': f'{score:.3f}',
                        'method': method,
                        'nces_unitid': unitid,
                        'nces_name': name,
                        'school_id': '',
                        'school_name': '',
                    }
                )
                continue

            matched += 1

            if not force:
                has_address = bool(school.street_address and school.city and school.state and school.zip_code)
                has_coords = school.latitude is not None and school.longitude is not None
                if has_address and has_coords and school.nces_unitid:
                    skipped += 1
                    report_rows.append(
                        {
                            'status': 'skipped',
                            'score': f'{score:.3f}',
                            'method': method,
                            'nces_unitid': unitid,
                            'nces_name': name,
                            'school_id': school.id,
                            'school_name': school.name,
                        }
                    )
                    continue

            needs_review = score < 0.92
            if needs_review:
                review += 1

            if not dry_run:
                school.nces_unitid = unitid
                school.nces_name = name
                school.nces_schoolyear = schoolyear

                school.street_address = street or school.street_address
                school.city = city or school.city
                school.state = state or school.state
                school.zip_code = zip_code or school.zip_code
                school.address_complete = full_address(
                    school.street_address,
                    school.city,
                    school.state,
                    school.zip_code,
                )

                if lat is not None and lon is not None:
                    school.latitude = float(lat)
                    school.longitude = float(lon)
                    school.geocode_raw = f'{lat}, {lon}'

                school.geocode_source = 'nces_arcgis'
                school.geocode_source_url = layer_url
                school.geocode_query = name
                school.geocode_confidence = score
                school.geocode_needs_review = needs_review
                school.geocode_status = (
                    School.GeocodeStatus.REVIEW if needs_review else School.GeocodeStatus.GEOCODED
                )
                school.geocode_notes = f'Imported from NCES via {method} match.'
                school.geocode_updated_at = timezone.now()

                school.save(
                    update_fields=[
                        'nces_unitid',
                        'nces_name',
                        'nces_schoolyear',
                        'street_address',
                        'city',
                        'state',
                        'zip_code',
                        'address_complete',
                        'latitude',
                        'longitude',
                        'geocode_raw',
                        'geocode_source',
                        'geocode_source_url',
                        'geocode_query',
                        'geocode_confidence',
                        'geocode_needs_review',
                        'geocode_status',
                        'geocode_notes',
                        'geocode_updated_at',
                    ]
                )
                schools_by_unitid[unitid] = school

            updated += 1
            report_rows.append(
                {
                    'status': 'updated',
                    'score': f'{score:.3f}',
                    'method': method,
                    'nces_unitid': unitid,
                    'nces_name': name,
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
                'Processed={} matched={} updated={} skipped={} review={} unmatched={} dry_run={}'.format(
                    processed,
                    matched,
                    updated,
                    skipped,
                    review,
                    unmatched,
                    dry_run,
                )
            )
        )
