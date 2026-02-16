# Project Skyway MVP

MVP stack:
- Frontend: Next.js + React
- Backend: Django + Django REST Framework
- Database: PostgreSQL
- Maps: OpenStreetMap via Leaflet
- Auth: Email/password + email verification + password reset
- Admin: Django Admin + CSV upload for schools

## 1. Backend setup

```bash
cd /Users/johnraisch/Documents/New\ project/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

API base: `http://localhost:8000/api`
Admin: `http://localhost:8000/admin`

### Import CSV
- In admin, go to Schools and click `Upload CSV`.
- Upload your file from `/Users/johnraisch/Downloads/Project Skyway - Schools.csv`.

Or CLI:

```bash
python manage.py import_schools_csv "/Users/johnraisch/Downloads/Project Skyway - Schools.csv"
```

## 2. Frontend setup

```bash
cd /Users/johnraisch/Documents/New\ project/frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Frontend runs at `http://localhost:3000`.

## Implemented v1 features
- Live filter/search (keyword on name/city/state)
- Filters: Team Type, Conference, Discipline, State
- Sort: relevance, distance, alphabetical
- Map + list synchronized results
- School detail page
- Student signup/login
- Email verification + password reset
- Favorites API with private/public visibility
- Public favorites endpoint support (`GET /api/favorites/?public=true`)

## Address Sourcing + Geocoding Workflow

The backend now includes two batch commands:

1. `enrich_addresses`
- Sources/normalizes address data (address, city, state, zip) using OpenStreetMap Nominatim.
- Stores provenance + confidence metadata for review.

2. `geocode_schools`
- Generates `latitude`/`longitude` for map pins.
- Flags low-confidence results for admin review.

### Recommended run sequence

1. Start with a dry-run sample:

```bash
cd /Users/johnraisch/Documents/New\ project/backend
source .venv/bin/activate
python manage.py enrich_addresses --limit 25 --sleep 1.1 --dry-run
python manage.py geocode_schools --limit 25 --sleep 1.1 --dry-run
```

2. Run enrichment for schools missing address fields:

```bash
python manage.py enrich_addresses --sleep 1.1 --threshold 0.75
```

3. Run geocoding for schools missing coordinates:

```bash
python manage.py geocode_schools --sleep 1.1 --threshold 0.75
```

### Useful flags
- `--limit N`: process only N rows.
- `--dry-run`: preview without saving.
- `--force`: include rows that already have values.
- `--threshold 0.75`: below threshold is marked for review.

### Admin review
- In Django Admin `Schools`, use filters:
  - `geocode_status`
  - `geocode_needs_review`

## NCES ArcGIS Import (IPEDS 2022-23)

Use NCES as the primary source for postsecondary addresses and coordinates.

Command:

```bash
cd /Users/johnraisch/Documents/New\ project/backend
source .venv/bin/activate
python manage.py import_nces_addresses --min-score 0.9 --report /Users/johnraisch/Documents/New\ project/reports/nces_import.csv
```

Useful flags:
- `--dry-run`: evaluate matches without writing.
- `--limit N`: process only first N NCES rows.
- `--min-score 0.86`: confidence threshold for accepting a match.
- `--force`: overwrite rows even if they already have address/coords.
- `--report PATH`: save row-level match decisions for audit/review.

## Notes
- CSV import is intentionally loose to tolerate incomplete data.
- Geocoding uses `Geocode` column when present; no external geocoding job is included.
- Fuzzy matching is currently lightweight (`icontains` + relevance heuristics).
