# Project Skyway MVP

MVP stack:
- Frontend: Next.js + React
- Backend: Django + Django REST Framework
- Database: PostgreSQL
- Maps: OpenStreetMap via Leaflet
- Auth: Email/password + email verification + password reset
- Admin: Django Admin + CSV upload for schools

## Quick start (one command)

From repo root:

```bash
./dev up
```

This command will:
- create env files if missing
- install backend/frontend dependencies
- run Django migrations
- start backend (`127.0.0.1:8000`) and frontend (`127.0.0.1:3000`) in background

Useful commands:

```bash
./dev status   # show service status
./dev logs     # tail backend/frontend logs
./dev down     # stop both services
./dev setup    # run setup only
./dev refresh  # hard reset local state, restart, then run doctor
```

Recommended daily flow:

```bash
make local       # runs ./dev refresh
make local-check # runs ./dev doctor
```

Logs are written to:
- `/tmp/skyway-backend.log`
- `/tmp/skyway-frontend.log`

## 1. Backend setup (manual)

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

## 2. Frontend setup (manual)

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

## Invitation Access Gate

- Entire frontend is gated by an invitation code modal.
- Django admin is exempt (`/admin` remains normal).
- Access code is sticky via cookie and device-bound.
- Default code expiration is one week.
- If expired, entering the same valid code renews it for another week.
- Success and failed attempts are logged with timestamp, client IP (`X-Forwarded-For` aware), device id, and source.

### Admin management

In Django Admin:
- `Accounts -> Access codes`: create/manage codes and invitee metadata.
- `Accounts -> Access code logs`: review successful passes and failed attempts.
- `Cms -> Site configuration`: toggle `Invitation code required` on/off by environment.

Useful admin actions on access codes:
- extend selected codes by one week
- enable/disable codes
- clear device binding

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
