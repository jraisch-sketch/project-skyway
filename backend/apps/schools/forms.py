from django import forms

from .models import ImportSchema


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(label='CSV file')


class DataLoadUploadForm(forms.Form):
    schema = forms.ModelChoiceField(
        queryset=ImportSchema.objects.none(),
        required=False,
        help_text='Use an existing schema definition.',
    )
    schema_file = forms.FileField(
        required=False,
        help_text='Upload a JSON schema file to create a new schema.',
    )
    schema_name = forms.CharField(
        required=False,
        max_length=150,
        help_text='Required when uploading a new schema file.',
    )
    schema_version = forms.CharField(required=False, max_length=50, initial='v1')
    csv_file = forms.FileField(label='Data CSV')
    dry_run = forms.BooleanField(
        required=False,
        initial=True,
        help_text='Dry run validates and previews create/update counts without database writes.',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['schema'].queryset = ImportSchema.objects.filter(active=True).order_by('name', 'version')

    def clean(self):
        cleaned = super().clean()
        schema = cleaned.get('schema')
        schema_file = cleaned.get('schema_file')
        schema_name = (cleaned.get('schema_name') or '').strip()
        dry_run = bool(cleaned.get('dry_run'))

        if not schema and not schema_file:
            raise forms.ValidationError('Choose an existing schema or upload a schema JSON file.')

        if schema_file and not schema_name:
            raise forms.ValidationError('Schema name is required when uploading a schema file.')

        if not dry_run and schema_file:
            raise forms.ValidationError('Create the schema with a dry run first, then commit.')

        return cleaned
