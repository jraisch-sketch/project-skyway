# Eastern Conference Discipline Research Runbook

## Goal

Identify supported cycling disciplines for each Eastern conference team using evidence-backed web research.

## Source file

- Research queue: `reports/eastern_csep_research_queue.csv` (64 teams)

## Recommended Deep Thinking Prompt

Use this prompt in ChatGPT for each school row:

```text
You are doing data QA for collegiate cycling teams.
School: <school_name>
School website: <school_website>
Cycling website: <cycling_website>

Task:
1) Find official or highly credible sources describing this team's disciplines.
2) Infer whether the team supports these disciplines: road, mtb_xc, mtb_st, mtb_enduro, mtb_downhill, mtb_slalom, cyclocross, track.
3) Return only evidence-backed values. If unclear, return unknown and explain.

Prioritize sources in this order:
- official school athletics/club pages
- official team pages/social profiles clearly linked from school pages
- USA Cycling collegiate pages or race/result pages
- conference pages (ECCC)

Output JSON:
{
  "school_name": "...",
  "evidence": [
    {
      "url": "...",
      "date": "YYYY-MM-DD or unknown",
      "snippet": "short supporting quote"
    }
  ],
  "disciplines": {
    "road": true|false|"unknown",
    "mtb_xc": true|false|"unknown",
    "mtb_st": true|false|"unknown",
    "mtb_enduro": true|false|"unknown",
    "mtb_downhill": true|false|"unknown",
    "mtb_slalom": true|false|"unknown",
    "cyclocross": true|false|"unknown",
    "track": true|false|"unknown"
  },
  "notes": "brief rationale"
}
```

## Row update rules for CSV

- `research_status`: `complete` or `needs-review`
- `evidence_url`: best primary source URL
- `evidence_date`: date from source if available
- `evidence_snippet`: short quoted phrase
- `discipline_evidence_text`: plain text summary of discipline evidence
- Discipline columns: `true`/`false` only when supported by evidence; leave blank if unknown
- `researcher`: `chatgpt-deep`
- `notes`: ambiguity or confidence notes

## Apply to database

Dry run:

```bash
cd "/Users/johnraisch/Documents/New project/backend"
source .venv/bin/activate
python manage.py apply_csep_research \
  --input "/Users/johnraisch/Documents/New project/reports/eastern_csep_research_queue.csv" \
  --dry-run \
  --report "/Users/johnraisch/Documents/New project/reports/eastern_csep_apply_dryrun.csv"
```

Live apply:

```bash
python manage.py apply_csep_research \
  --input "/Users/johnraisch/Documents/New project/reports/eastern_csep_research_queue.csv" \
  --report "/Users/johnraisch/Documents/New project/reports/eastern_csep_apply_live.csv"
```
