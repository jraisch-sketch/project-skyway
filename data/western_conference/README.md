# Western Conference Data Workspace

This folder is the structured working area for Western Conference school data tasks.

## Files
- `western_conference_contacts.csv`: source-of-truth seed list from provided school/contact data.
- `western_conference_task_queue.csv`: iterative research/update queue with status tracking.
- `western_scorecard_enrichment_latest.csv`: latest non-cycling field enrichment from College Scorecard Open Data API.
- `western_scorecard_enrichment_YYYYMMDD-HHMMSS.csv`: timestamped enrichment snapshots.
- `western_geocode_results_latest.csv`: latest latitude/longitude enrichment output from Nominatim.
- `western_geocode_needs_review_latest.csv`: subset of geocode rows below confidence threshold.
- `western_csep_research_queue.csv`: current working queue for cycling-discipline research/evidence.
- `western_csep_research_batch1_conference_seed.csv`: initial conference-level discipline seed (provisional).

## Workflow
1. Keep raw inputs in `western_conference_contacts.csv`.
2. Track enrichment work in `western_conference_task_queue.csv`.
3. Add new outputs for each batch in this folder (for example: `western_discipline_research_batch1_YYYY-MM-DD.csv`).
4. For non-cycling profile enrichment, run:
   `python3 scripts/western_scorecard_enrich.py --api-key "$COLLEGE_SCORECARD_API_KEY"`
5. For geocoding from the scorecard-enriched dataset, run:
   `python3 scripts/western_geocode_from_scorecard.py --threshold 0.75 --sleep 0.3`
6. For discipline seeding/research apply (local):
   `python manage.py apply_csep_research --input ../data/western_conference/western_csep_research_queue.csv --no-infer --dry-run --report ../reports/western_csep_apply_dryrun.csv`
   Then run without `--dry-run` for local commit.

## Notes
- Keep `school_name` as the canonical matching field to existing `School` rows.
- Use lowercase emails for consistency.
- Scorecard fields captured align with `School` model non-cycling fields:
  `nces_unitid/id`, `nces_name`, `city`, `state`, `zip_code`, `school_website`,
  `institution_control`, `institution_level`, `locale`, `enrollment`,
  `acceptance_rate`, `graduation_rate`, `avg_cost`.
- Geocode fields captured align with `School` geocode fields:
  `latitude`, `longitude`, `geocode_raw`, `geocode_confidence`, `geocode_status`,
  `geocode_needs_review`, `geocode_query`, `geocode_source`, `geocode_source_url`,
  `address_complete`.
- Current discipline seed is conference-level evidence and marked `needs-review`.
  Treat as provisional until team-level sources are added per school.
