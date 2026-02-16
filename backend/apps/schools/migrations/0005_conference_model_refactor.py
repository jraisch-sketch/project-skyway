from django.db import migrations, models
import django.db.models.deletion


def forward_copy_conferences(apps, schema_editor):
    School = apps.get_model('schools', 'School')
    Conference = apps.get_model('schools', 'Conference')

    for school in School.objects.all().iterator():
        raw_name = (school.conference or '').strip()
        if not raw_name:
            continue
        conference, _ = Conference.objects.get_or_create(name=raw_name)
        school.conference_fk_id = conference.id
        school.save(update_fields=['conference_fk'])


def reverse_copy_conferences(apps, schema_editor):
    School = apps.get_model('schools', 'School')
    Conference = apps.get_model('schools', 'Conference')

    conference_by_id = {conf.id: conf.name for conf in Conference.objects.all()}
    for school in School.objects.all().iterator():
        conf_name = conference_by_id.get(school.conference_fk_id, '')
        school.conference = conf_name
        school.save(update_fields=['conference'])


class Migration(migrations.Migration):
    dependencies = [
        ('schools', '0004_school_cycling_program_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='Conference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, unique=True)),
                ('description', models.TextField(blank=True)),
                ('contact_name', models.CharField(blank=True, max_length=255)),
                ('contact_email', models.EmailField(blank=True, max_length=254)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.AddField(
            model_name='school',
            name='conference_fk',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='schools',
                to='schools.conference',
            ),
        ),
        migrations.RunPython(forward_copy_conferences, reverse_copy_conferences),
        migrations.RemoveField(
            model_name='school',
            name='conference',
        ),
        migrations.RenameField(
            model_name='school',
            old_name='conference_fk',
            new_name='conference',
        ),
    ]
