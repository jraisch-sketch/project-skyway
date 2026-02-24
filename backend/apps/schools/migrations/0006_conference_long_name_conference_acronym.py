from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0005_conference_model_refactor'),
    ]

    operations = [
        migrations.AddField(
            model_name='conference',
            name='acronym',
            field=models.CharField(blank=True, db_index=True, max_length=30),
        ),
        migrations.AddField(
            model_name='conference',
            name='long_name',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
