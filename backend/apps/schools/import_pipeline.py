import csv
import io
import json
from datetime import datetime

from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from .models import Conference, DataLoadJob, ImportSchema, School

SUPPORTED_TARGET_MODEL = 'schools.School'
ALLOWED_UNIQUE_KEYS = (['nces_unitid'], ['name', 'state'])


def parse_bool(value):
    if isinstance(value, bool):
        return value
    text = (value or '').strip().lower()
    return text in {'1', 'true', 'yes', 'y', 'x'}


def parse_date(value):
    text = (value or '').strip()
    if not text:
        return None
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y'):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError(f'Unsupported date format: {value}')


def parse_csv_rows(file_obj):
    file_obj.seek(0)
    decoded = file_obj.read().decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(decoded))
    for idx, row in enumerate(reader, start=2):
        yield idx, row


def parse_schema_json_file(file_obj):
    file_obj.seek(0)
    payload = file_obj.read().decode('utf-8-sig')
    return json.loads(payload)


def normalize_schema_config(schema: ImportSchema):
    mapping = schema.mapping_json or {}
    unique_key_fields = schema.unique_key_fields or []
    required_fields = schema.required_fields or []
    defaults = schema.defaults_json or {}
    type_rules = schema.type_rules or {}

    if schema.target_model != SUPPORTED_TARGET_MODEL:
        raise ValueError(f'Unsupported target_model: {schema.target_model}')
    if not isinstance(mapping, dict) or not mapping:
        raise ValueError('Schema must include a non-empty mapping_json object.')
    if unique_key_fields not in ALLOWED_UNIQUE_KEYS:
        raise ValueError('unique_key_fields must be ["nces_unitid"] or ["name", "state"].')

    allowed_fields = {
        f.name for f in School._meta.fields
        if f.editable and f.name not in {'id', 'created_at', 'updated_at', 'logo'}
    }
    unknown_fields = sorted({field for field in mapping.values() if field not in allowed_fields})
    if unknown_fields:
        raise ValueError(f'Unknown mapped fields: {", ".join(unknown_fields)}')
    unknown_default_fields = sorted({field for field in defaults if field not in allowed_fields})
    if unknown_default_fields:
        raise ValueError(f'Unknown default fields: {", ".join(unknown_default_fields)}')
    unknown_typed_fields = sorted({field for field in type_rules if field not in allowed_fields})
    if unknown_typed_fields:
        raise ValueError(f'Unknown type_rules fields: {", ".join(unknown_typed_fields)}')

    return {
        'mapping': mapping,
        'unique_key_fields': unique_key_fields,
        'required_fields': required_fields,
        'defaults': defaults,
        'type_rules': type_rules,
    }


def convert_value(field, raw_value, type_rule=''):
    if raw_value is None:
        return None
    if isinstance(raw_value, str):
        raw_value = raw_value.strip()

    if raw_value == '':
        return None

    if type_rule == 'string':
        return str(raw_value).strip()
    if type_rule == 'int':
        return int(raw_value)
    if type_rule == 'float':
        return float(raw_value)
    if type_rule == 'bool':
        return parse_bool(raw_value)
    if type_rule == 'date':
        return parse_date(raw_value)

    internal_type = field.get_internal_type()
    if internal_type in {'BooleanField'}:
        return parse_bool(raw_value)
    if internal_type in {'PositiveIntegerField', 'IntegerField'}:
        return int(raw_value)
    if internal_type in {'FloatField', 'DecimalField'}:
        return float(raw_value)
    if internal_type in {'DateField'}:
        return parse_date(raw_value)
    if field.name == 'conference':
        return str(raw_value).strip()

    value = str(raw_value).strip()
    if getattr(field, 'choices', None):
        choices = dict(field.choices)
        if value in choices:
            return value
        for key, label in choices.items():
            if value.lower() == str(label).lower():
                return key
    return value


def map_row_to_school_values(raw_row, schema_config):
    mapping = schema_config['mapping']
    defaults = schema_config['defaults']
    type_rules = schema_config['type_rules']

    values = {}
    for source_column, model_field in mapping.items():
        field = School._meta.get_field(model_field)
        raw_value = raw_row.get(source_column)
        converted = convert_value(field, raw_value, type_rules.get(model_field, ''))
        if converted is not None:
            values[model_field] = converted

    for field_name, default_value in defaults.items():
        if field_name not in values or values[field_name] is None:
            field = School._meta.get_field(field_name)
            values[field_name] = convert_value(field, default_value, type_rules.get(field_name, ''))

    return values


def resolve_lookup(values, unique_key_fields):
    lookup = {}
    for key in unique_key_fields:
        value = values.get(key)
        if value in (None, ''):
            raise ValueError(f'Missing unique key field: {key}')
        lookup[key] = value
    return lookup


def validate_values(values, schema_config):
    required_fields = schema_config['required_fields']
    missing = [field for field in required_fields if not values.get(field)]
    if missing:
        raise ValueError(f'Missing required fields: {", ".join(missing)}')


def _save_report(job, results):
    buffer = io.StringIO()
    fieldnames = ['row_number', 'status', 'action', 'lookup', 'message']
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for row in results:
        writer.writerow(row)

    filename = f'data_load_job_{job.id}_report.csv'
    job.report_file.save(filename, ContentFile(buffer.getvalue()), save=False)


def run_data_load_job(job: DataLoadJob):
    job.status = DataLoadJob.Status.RUNNING
    job.error_message = ''
    job.started_at = timezone.now()
    job.finished_at = None
    job.created_count = 0
    job.updated_count = 0
    job.error_count = 0
    job.save(update_fields=[
        'status',
        'error_message',
        'started_at',
        'finished_at',
        'created_count',
        'updated_count',
        'error_count',
    ])

    try:
        schema_config = normalize_schema_config(job.schema)
        results = []
        created_count = 0
        updated_count = 0
        error_count = 0

        job.uploaded_file.open('rb')
        try:
            for row_number, raw_row in parse_csv_rows(job.uploaded_file):
                try:
                    values = map_row_to_school_values(raw_row, schema_config)
                    validate_values(values, schema_config)
                    lookup = resolve_lookup(values, schema_config['unique_key_fields'])
                    lookup_text = ', '.join(f'{k}={lookup[k]}' for k in lookup)

                    matches = School.objects.filter(**lookup)
                    if matches.count() > 1:
                        raise ValueError(f'Lookup matched multiple schools: {lookup_text}')
                    existing = matches.first()
                    action = 'update' if existing else 'create'
                    if job.dry_run:
                        if action == 'create':
                            created_count += 1
                        else:
                            updated_count += 1
                        results.append({
                            'row_number': row_number,
                            'status': 'ok',
                            'action': action,
                            'lookup': lookup_text,
                            'message': 'Dry run validated successfully.',
                        })
                        continue

                    with transaction.atomic():
                        payload = values.copy()
                        conference_name = payload.pop('conference', None)
                        if conference_name:
                            conference, _ = Conference.objects.get_or_create(name=conference_name)
                            payload['conference'] = conference

                        if existing:
                            for field_name, field_value in payload.items():
                                setattr(existing, field_name, field_value)
                            existing.save()
                            updated_count += 1
                        else:
                            School.objects.create(**payload)
                            created_count += 1

                    results.append({
                        'row_number': row_number,
                        'status': 'ok',
                        'action': action,
                        'lookup': lookup_text,
                        'message': 'Committed successfully.',
                    })
                except Exception as exc:
                    error_count += 1
                    results.append({
                        'row_number': row_number,
                        'status': 'error',
                        'action': 'skipped',
                        'lookup': '',
                        'message': str(exc),
                    })
        finally:
            job.uploaded_file.close()

        job.created_count = created_count
        job.updated_count = updated_count
        job.error_count = error_count
        job.status = DataLoadJob.Status.COMPLETED
        _save_report(job, results)
    except Exception as exc:
        job.status = DataLoadJob.Status.FAILED
        job.error_message = str(exc)
    finally:
        job.finished_at = timezone.now()
        job.save()

    return job
