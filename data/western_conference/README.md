# Western Conference Data Workspace

This folder is the structured working area for Western Conference school data tasks.

## Files
- `western_conference_contacts.csv`: source-of-truth seed list from provided school/contact data.
- `western_conference_task_queue.csv`: iterative research/update queue with status tracking.
- `western_scorecard_enrichment_latest.csv`: latest non-cycling field enrichment from College Scorecard Open Data API.
- `western_scorecard_enrichment_YYYYMMDD-HHMMSS.csv`: timestamped enrichment snapshots.

## Workflow
1. Keep raw inputs in `western_conference_contacts.csv`.
2. Track enrichment work in `western_conference_task_queue.csv`.
3. Add new outputs for each batch in this folder (for example: `western_discipline_research_batch1_YYYY-MM-DD.csv`).
4. For non-cycling profile enrichment, run:
   `python3 scripts/western_scorecard_enrich.py --api-key "$COLLEGE_SCORECARD_API_KEY"`

## Notes
- Keep `school_name` as the canonical matching field to existing `School` rows.
- Use lowercase emails for consistency.
- Scorecard fields captured align with `School` model non-cycling fields:
  `nces_unitid/id`, `nces_name`, `city`, `state`, `zip_code`, `school_website`,
  `institution_control`, `institution_level`, `locale`, `enrollment`,
  `acceptance_rate`, `graduation_rate`, `avg_cost`.
