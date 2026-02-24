from django.core.management.base import BaseCommand

from apps.schools.models import Conference


CONFERENCE_DATA = [
    {
        'name': 'Atlantic',
        'aliases': ['atlantic'],
        'long_name': 'Atlantic Collegiate Cycling Conference',
        'acronym': 'ACCC',
        'description': (
            'Mid-Atlantic USA Cycling collegiate conference with schools from states like '
            'Virginia, Maryland, and North Carolina, focused on road, MTB, and cyclocross.'
        ),
    },
    {
        'name': 'Eastern',
        'aliases': ['eastern'],
        'long_name': 'Eastern Collegiate Cycling Conference',
        'acronym': 'ECCC',
        'description': (
            'Northeast conference spanning Delaware to Maine, with 50+ schools competing '
            'across track, MTB, cyclocross, and road through the year.'
        ),
    },
    {
        'name': 'Inter Mountain',
        'aliases': ['inter mountain', 'intermountain'],
        'long_name': 'Intermountain Collegiate Cycling Conference',
        'acronym': 'IMCCC',
        'description': (
            'Intermountain West conference supporting road, MTB, BMX, track, and cyclocross '
            'racing and collegiate community.'
        ),
    },
    {
        'name': 'Midwest',
        'aliases': ['midwest'],
        'long_name': 'Midwest Collegiate Cycling Conference',
        'acronym': 'MWCCC',
        'description': (
            'Midwest conference supporting road, MTB, BMX, track, cyclocross, and gravel racing, '
            'plus collegiate team community across the region.'
        ),
    },
    {
        'name': 'North Central',
        'aliases': ['north central'],
        'long_name': 'North Central Collegiate Cycling Conference',
        'acronym': 'NCCCC',
        'description': (
            'North Central conference supporting road, MTB, BMX, track, cyclocross, and gravel '
            'racing while building a collegiate cycling community.'
        ),
    },
    {
        'name': 'Northwest',
        'aliases': ['northwest'],
        'long_name': 'Northwest Collegiate Cycling Conference',
        'acronym': 'NWCCC',
        'description': (
            'Northwest conference supporting road, MTB, BMX, track, cyclocross, and gravel racing '
            'and collegiate cycling community across the region.'
        ),
    },
    {
        'name': 'Rocky Mountain',
        'aliases': ['rocky mountain'],
        'long_name': 'Rocky Mountain Collegiate Cycling Conference',
        'acronym': 'RMCCC',
        'description': (
            'Rocky Mountain region conference supporting collegiate road, MTB, and track racing '
            'with an emphasis on a fun, fair, competitive experience.'
        ),
    },
    {
        'name': 'South Central',
        'aliases': ['south central'],
        'long_name': 'South Central Collegiate Cycling Conference',
        'acronym': 'SCCCC',
        'description': (
            'South Central conference with teams from Texas, Oklahoma, Arkansas, Louisiana, '
            'and beyond, supporting road, MTB, BMX, track, and cyclocross.'
        ),
    },
    {
        'name': 'Southeast',
        'aliases': ['southeast', 'southeastern'],
        'long_name': 'Southeastern Collegiate Cycling Conference',
        'acronym': 'SECCC',
        'description': (
            'Southeast conference with schools from Alabama, Georgia, Florida, and beyond, '
            'supporting road, MTB, BMX, track, and cyclocross.'
        ),
    },
    {
        'name': 'Southwest',
        'aliases': ['southwest', 'southwes'],
        'long_name': 'Southwest Collegiate Cycling Conference',
        'acronym': 'SWCCC',
        'description': (
            'Southwest conference including Arizona, New Mexico, and West Texas, with athletes '
            'competing in road, MTB, track, BMX, and cyclocross.'
        ),
    },
    {
        'name': 'Western',
        'aliases': ['western'],
        'long_name': 'Western Collegiate Cycling Conference',
        'acronym': 'WCCC',
        'description': (
            'West Coast conference representing schools from California, Hawaii, and the western '
            'half of Nevada, supporting road, MTB, BMX, track, and cyclocross.'
        ),
    },
]


def _normalize(value: str) -> str:
    return (value or '').strip().lower()


class Command(BaseCommand):
    help = 'Upsert conference long_name, acronym, and description from a predefined dataset.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--no-create', action='store_true', help='Do not create missing conferences.')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        allow_create = not options['no_create']

        existing = { _normalize(c.name): c for c in Conference.objects.all() }
        updated = 0
        created = 0
        skipped = 0

        for row in CONFERENCE_DATA:
            keys = {_normalize(row['name'])}
            keys.update(_normalize(alias) for alias in row.get('aliases', []))

            conference = None
            for key in keys:
                if key in existing:
                    conference = existing[key]
                    break

            if conference is None:
                if not allow_create:
                    skipped += 1
                    self.stdout.write(f"Skipped (missing): {row['name']}")
                    continue
                conference = Conference(name=row['name'])
                if not dry_run:
                    conference.save()
                    existing[_normalize(conference.name)] = conference
                created += 1
                self.stdout.write(f"Created: {row['name']}")

            conference.long_name = row['long_name']
            conference.acronym = row['acronym']
            conference.description = row['description']

            if not dry_run:
                conference.save(update_fields=['long_name', 'acronym', 'description', 'updated_at'])
            updated += 1
            self.stdout.write(f"Updated: {conference.name} ({conference.acronym})")

        self.stdout.write(
            self.style.SUCCESS(
                f'Conference metadata upsert complete: updated={updated} created={created} skipped={skipped} dry_run={dry_run}'
            )
        )
