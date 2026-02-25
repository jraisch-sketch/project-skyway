# CSEP (Cycling-Specific Enrichment Process)

CSEP is a research-assisted data enrichment workflow for cycling-specific school profile fields.

## Current CSEP fields (strawman v1)

- Discipline booleans:
  - `road`
  - `mtb_xc`
  - `mtb_st`
  - `mtb_enduro`
  - `mtb_downhill`
  - `mtb_slalom`
  - `cyclocross`
- Program status:
  - `cycling_program_status` (`active`, `inactive`, `unknown`)
- Staff/contact:
  - `head_coach`
  - `contact_email`

## Decision rules

1. Discipline booleans
- Set discipline boolean to `True` when research evidence contains discipline-specific keywords.
- Default behavior is non-destructive: absent/weak evidence does not auto-force `False` unless `--force` is explicitly used.

2. Cycling program status
- Set `cycling_program_status=active` when a reliable online source shows team activity in calendar year **2025**.
- If no evidence of activity is found, set to `unknown` or `inactive` per researcher determination.

3. Head coach
- Populate `head_coach` only when named on official school/team pages or reliable governing/team sources.

4. Contact email
- Populate `contact_email` when a valid email is found for the cycling head coach or team contact.

## Local workflow

1. Export a research queue template from local DB:

```bash
cd "/Users/johnraisch/Documents/New project/backend"
source .venv/bin/activate
python manage.py export_csep_template --limit 50 --out "/Users/johnraisch/Documents/New project/reports/csep_research_queue.csv"
```

2. Research each row and fill evidence columns in the CSV.

3. Apply with dry-run first:

```bash
python manage.py apply_csep_research \
  --input "/Users/johnraisch/Documents/New project/reports/csep_research_queue.csv" \
  --dry-run \
  --report "/Users/johnraisch/Documents/New project/reports/csep_apply_dryrun.csv"
```

4. Apply live:

```bash
python manage.py apply_csep_research \
  --input "/Users/johnraisch/Documents/New project/reports/csep_research_queue.csv" \
  --report "/Users/johnraisch/Documents/New project/reports/csep_apply_live.csv"
```

## Suggested Thinking Mode research prompt

Use this in ChatGPT Thinking Mode per school row:

- Find official/credible sources for this school's cycling program.
- Identify discipline evidence keywords and 2025 activity evidence.
- Return: evidence URL, evidence date, short evidence snippet, inferred disciplines, program status, head coach, contact email.
- Prefer official school athletics pages, team pages, conference pages, and trustworthy race/result sources.
