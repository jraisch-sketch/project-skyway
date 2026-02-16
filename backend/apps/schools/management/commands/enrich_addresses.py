from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from apps.schools.geocoding import (
    build_enrichment_queries,
    choose_best_candidate,
    nominatim_search,
    osm_source_url,
    result_city_state_zip,
    throttle,
)
from apps.schools.models import School


class Command(BaseCommand):
    help = 'Source missing address data from OpenStreetMap Nominatim.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=0)
        parser.add_argument('--sleep', type=float, default=1.0)
        parser.add_argument('--threshold', type=float, default=0.75)
        parser.add_argument('--countrycodes', type=str, default='us')
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--force', action='store_true')

    def handle(self, *args, **options):
        limit = options['limit']
        sleep_seconds = options['sleep']
        threshold = options['threshold']
        countrycodes = options['countrycodes']
        dry_run = options['dry_run']
        force = options['force']

        queryset = School.objects.all().order_by('id')
        if not force:
            queryset = queryset.filter(
                Q(address_complete='') | Q(city='') | Q(state='') | Q(zip_code='')
            )
        if limit > 0:
            queryset = queryset[:limit]

        processed = 0
        updated = 0
        review = 0
        failed = 0

        for school in queryset:
            processed += 1
            queries = build_enrichment_queries(school)
            best = None
            best_score = 0.0
            best_query = ''

            for query in queries:
                results = nominatim_search(query=query, limit=3, countrycodes=countrycodes)
                candidate, score = choose_best_candidate(school=school, query=query, results=results)
                if candidate and score > best_score:
                    best = candidate
                    best_score = score
                    best_query = query
                if best_score >= threshold:
                    break
                throttle(sleep_seconds)

            if not best:
                failed += 1
                if not dry_run:
                    school.geocode_status = School.GeocodeStatus.FAILED
                    school.geocode_notes = 'No address candidates found via Nominatim.'
                    school.geocode_updated_at = timezone.now()
                    school.save(update_fields=['geocode_status', 'geocode_notes', 'geocode_updated_at'])
                continue

            city, state, postcode = result_city_state_zip(best)
            needs_review = best_score < threshold

            if not dry_run:
                if not school.address_complete or force:
                    school.address_complete = best.get('display_name', '')
                if (not school.city or force) and city:
                    school.city = city
                if (not school.state or force) and state:
                    school.state = state
                if (not school.zip_code or force) and postcode:
                    school.zip_code = postcode

                school.geocode_query = best_query
                school.geocode_confidence = best_score
                school.geocode_source = 'nominatim'
                school.geocode_source_url = osm_source_url(best)
                school.geocode_needs_review = needs_review
                school.geocode_status = (
                    School.GeocodeStatus.REVIEW if needs_review else School.GeocodeStatus.ENRICHED
                )
                school.geocode_notes = 'Address candidate sourced from Nominatim.'
                school.geocode_updated_at = timezone.now()
                school.save(
                    update_fields=[
                        'address_complete',
                        'city',
                        'state',
                        'zip_code',
                        'geocode_query',
                        'geocode_confidence',
                        'geocode_source',
                        'geocode_source_url',
                        'geocode_needs_review',
                        'geocode_status',
                        'geocode_notes',
                        'geocode_updated_at',
                    ]
                )

            if needs_review:
                review += 1
            else:
                updated += 1

            self.stdout.write(
                f"[{processed}] {school.name}: confidence={best_score:.2f} review={needs_review}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Processed={processed} updated={updated} review={review} failed={failed} dry_run={dry_run}'
            )
        )
