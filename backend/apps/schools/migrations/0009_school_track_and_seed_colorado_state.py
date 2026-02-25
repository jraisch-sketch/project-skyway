from django.db import migrations, models


def seed_colorado_state_track(apps, schema_editor):
    School = apps.get_model('schools', 'School')
    School.objects.filter(name__iexact='Colorado State University').update(track=True)


def unseed_colorado_state_track(apps, schema_editor):
    School = apps.get_model('schools', 'School')
    School.objects.filter(name__iexact='Colorado State University').update(track=False)


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0008_importschema_dataloadjob'),
    ]

    operations = [
        migrations.AddField(
            model_name='school',
            name='track',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(seed_colorado_state_track, unseed_colorado_state_track),
    ]
