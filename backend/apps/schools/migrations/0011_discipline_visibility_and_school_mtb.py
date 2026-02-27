from django.db import migrations, models
from django.db.models import Q


DISCIPLINE_SEED_DATA = [
    ('road', 'Road', False, 10),
    ('mtb', 'MTB', False, 20),
    ('mtb_xc', 'MTB XC', True, 30),
    ('mtb_st', 'MTB Short Track', True, 40),
    ('mtb_enduro', 'MTB Enduro', True, 50),
    ('mtb_downhill', 'MTB Downhill', True, 60),
    ('mtb_slalom', 'MTB Slalom', True, 65),
    ('cyclocross', 'Cyclocross', False, 70),
    ('track', 'Track', False, 80),
]


def seed_disciplines_and_backfill_mtb(apps, schema_editor):
    Discipline = apps.get_model('schools', 'Discipline')
    School = apps.get_model('schools', 'School')

    for key, label, hidden, sort_order in DISCIPLINE_SEED_DATA:
        Discipline.objects.update_or_create(
            key=key,
            defaults={'label': label, 'hidden': hidden, 'sort_order': sort_order},
        )

    School.objects.filter(
        Q(mtb=True)
        | Q(mtb_xc=True)
        | Q(mtb_st=True)
        | Q(mtb_enduro=True)
        | Q(mtb_downhill=True)
        | Q(mtb_slalom=True)
    ).update(mtb=True)


def reverse_seed_disciplines_and_mtb(apps, schema_editor):
    Discipline = apps.get_model('schools', 'Discipline')
    School = apps.get_model('schools', 'School')
    keys = [row[0] for row in DISCIPLINE_SEED_DATA]
    Discipline.objects.filter(key__in=keys).delete()
    School.objects.all().update(mtb=False)


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0010_school_hidden'),
    ]

    operations = [
        migrations.CreateModel(
            name='Discipline',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=50, unique=True)),
                ('label', models.CharField(max_length=80)),
                ('hidden', models.BooleanField(db_index=True, default=False)),
                ('sort_order', models.PositiveIntegerField(db_index=True, default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['sort_order', 'label'],
            },
        ),
        migrations.AddField(
            model_name='school',
            name='mtb',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(seed_disciplines_and_backfill_mtb, reverse_seed_disciplines_and_mtb),
    ]
