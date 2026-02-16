import csv
from datetime import datetime

from .models import Conference, School


def parse_date(value: str):
    value = (value or '').strip()
    if not value:
        return None
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y'):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def parse_bool(value: str) -> bool:
    value = (value or '').strip().lower()
    return value in {'1', 'true', 'yes', 'y', 'x'}


def parse_geocode(value: str):
    value = (value or '').strip()
    if not value:
        return None, None
    parts = [p.strip() for p in value.replace(';', ',').split(',')]
    if len(parts) < 2:
        return None, None
    try:
        return float(parts[0]), float(parts[1])
    except ValueError:
        return None, None


def import_schools_from_csv(file_obj):
    decoded = file_obj.read().decode('utf-8-sig').splitlines()
    reader = csv.DictReader(decoded)
    imported = 0

    for row in reader:
        name = (row.get('SCHOOL NAME') or '').strip()
        if not name:
            continue

        team_type = (row.get('Club v Varsity') or '').strip()
        if team_type not in dict(School.TeamType.choices):
            team_type = ''
        conference_name = (row.get('CONFERENCE') or '').strip()
        conference = None
        if conference_name:
            conference, _ = Conference.objects.get_or_create(name=conference_name)

        latitude, longitude = parse_geocode(row.get('Geocode') or '')
        has_coords = latitude is not None and longitude is not None

        School.objects.update_or_create(
            name=name,
            defaults={
                'proto_data': row.get('Protodata', ''),
                'conference': conference,
                'team_type': team_type,
                'roster_male': int(row['Roster Male']) if (row.get('Roster Male') or '').isdigit() else None,
                'roster_female': int(row['Roster Female']) if (row.get('Roster Female') or '').isdigit() else None,
                'contact_email': row.get('CONTACT EMAIL', ''),
                'date_joined': parse_date(row.get('DATE JOINED', '')),
                'last_current': parse_date(row.get('LAST CURRENT', '')),
                'mascot': row.get('Mascot', ''),
                'school_website': row.get('School Website', ''),
                'athletic_dept_website': row.get('Athletic Dept Website', ''),
                'cycling_website': row.get('Cycling Website', ''),
                'street_address': row.get('Street address', ''),
                'city': row.get('City', ''),
                'state': row.get('State', ''),
                'zip_code': row.get('Zip', ''),
                'address_complete': row.get('Address complete', ''),
                'geocode_raw': row.get('Geocode', ''),
                'latitude': latitude,
                'longitude': longitude,
                'geocode_status': School.GeocodeStatus.GEOCODED if has_coords else School.GeocodeStatus.PENDING,
                'geocode_confidence': 1.0 if has_coords else None,
                'geocode_source': 'csv' if has_coords else '',
                'geocode_needs_review': False,
                'geocode_notes': 'Coordinates provided by CSV import.' if has_coords else '',
                'road': parse_bool(row.get('Road', '')),
                'mtb_xc': parse_bool(row.get('MTB XC', '')),
                'mtb_st': parse_bool(row.get('MTB ST', '')),
                'mtb_enduro': parse_bool(row.get('MTB Enduro', '')),
                'mtb_downhill': parse_bool(row.get('MTB Downhill', '')),
                'mtb_slalom': parse_bool(row.get('MTB Slalom', '')),
                'head_coach': row.get('Head Coach', ''),
                'instagram': row.get('Instagram', ''),
                'facebook': row.get('Facebook', ''),
                'twitter': row.get('Twitter', ''),
                'program_strengths': row.get('Program Strengths', ''),
                'avg_cost': row.get('Avg Cost', ''),
                'enrollment': row.get('Enrollment', ''),
                'acceptance_rate': row.get('Acceptance Rate', ''),
                'graduation_rate': row.get('Graduation Rate', ''),
                'cyclocross': parse_bool(row.get('Cyclocross', '')),
            },
        )
        imported += 1

    return imported
