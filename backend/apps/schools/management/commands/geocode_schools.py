from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.schools.geocoding import (
    build_enrichment_queries,
    choose_best_candidate,
    nominatim_search,
    osm_source_url,
    throttle,
)
from apps.schools.models import School


class Command(BaseCommand):
    help = 'Geocode schools and store latitude/longitude.'

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
            queryset = queryset.filter(latitude__isnull=True, longitude__isnull=True)
        if limit > 0:
            queryset = queryset[:limit]

        processed = 0
        geocoded = 0
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
                    school.geocode_notes = 'No geocode candidate found via Nominatim.'
                    school.geocode_updated_at = timezone.now()
                    school.save(update_fields=['geocode_status', 'geocode_notes', 'geocode_updated_at'])
                continue

            needs_review = best_score < threshold

            if not dry_run:
                school.latitude = float(best['lat'])
                school.longitude = float(best['lon'])
                school.geocode_raw = f"{best['lat']}, {best['lon']}"
                school.geocode_query = best_query
                school.geocode_confidence = best_score
                school.geocode_source = 'nominatim'
                school.geocode_source_url = osm_source_url(best)
                school.geocode_needs_review = needs_review
                school.geocode_status = (
                    School.GeocodeStatus.REVIEW if needs_review else School.GeocodeStatus.GEOCODED
                )
                school.geocode_notes = 'Coordinates generated from Nominatim.'
                school.geocode_updated_at = timezone.now()
                school.save(
                    update_fields=[
                        'latitude',
                        'longitude',
                        'geocode_raw',
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
                geocoded += 1

            self.stdout.write(
                f"[{processed}] {school.name}: lat={best['lat']} lon={best['lon']} confidence={best_score:.2f} review={needs_review}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Processed={processed} geocoded={geocoded} review={review} failed={failed} dry_run={dry_run}'
            )
        )
