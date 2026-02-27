# Western Conference Data Workspace

This folder is the structured working area for Western Conference school data tasks.

## Files
- `western_conference_contacts.csv`: source-of-truth seed list from provided school/contact data.
- `western_conference_task_queue.csv`: iterative research/update queue with status tracking.

## Workflow
1. Keep raw inputs in `western_conference_contacts.csv`.
2. Track enrichment work in `western_conference_task_queue.csv`.
3. Add new outputs for each batch in this folder (for example: `western_discipline_research_batch1_YYYY-MM-DD.csv`).

## Notes
- Keep `school_name` as the canonical matching field to existing `School` rows.
- Use lowercase emails for consistency.
- Do not delete prior batch output files; append new batch files for traceability.
