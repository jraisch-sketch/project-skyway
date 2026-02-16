from django.core.management.base import BaseCommand, CommandError

from apps.schools.csv_import import import_schools_from_csv


class Command(BaseCommand):
    help = 'Import schools from a CSV file.'

    def add_arguments(self, parser):
        parser.add_argument('csv_path', type=str)

    def handle(self, *args, **options):
        csv_path = options['csv_path']
        try:
            with open(csv_path, 'rb') as file_obj:
                imported = import_schools_from_csv(file_obj)
            self.stdout.write(self.style.SUCCESS(f'Imported/updated {imported} schools.'))
        except FileNotFoundError as exc:
            raise CommandError(f'CSV file not found: {csv_path}') from exc
