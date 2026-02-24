# Data Gap Register + Django Admin Loader Playbook

This gives you:
1. A repeatable template/process for data-gap closure.
2. A concrete automation design for schema-driven imports in Django Admin.

## 1) Templates to Use Now

- Gap register: `/Users/johnraisch/Documents/New project/reports/templates/data_gap_register_template.csv`
- Weekly scorecard: `/Users/johnraisch/Documents/New project/reports/templates/data_quality_scorecard_template.csv`

### Gap register column intent
- `gap_id`: Stable ID (`GAP-###`) used in standups.
- `gap_type`: `missing_rows | missing_field | stale_values | inconsistent_ids | duplicates | schema_drift`.
- `expected_rule`: Machine-checkable expectation.
- `actual_observation`: What you measured.
- `coverage_pct`: Percent currently meeting rule.
- `severity`: `high | medium | low`.
- `priority`: `P0 | P1 | P2`.
- `fill_strategy`: `backfill | source_expansion | inference | fallback_ux`.
- `validation_rule`: Exact pass/fail rule for done-state.

## 2) Fill Workflow (Use With ChatGPT Thinking Mode)

1. Export a profiling slice (one dataset/field cohort at a time).
2. Add one row per meaningful gap in the register.
3. Ask ChatGPT to classify each gap into root causes and propose:
   - fastest safe fix
   - highest-confidence source
   - validation tests
4. Bring recommendations back to this repo as actionable issues/commands.
5. Track weekly movement in the scorecard CSV.

### Prompt seed you can paste into ChatGPT web

```text
You are my data quality copilot. I will provide rows from a Data Gap Register.
For each row, return:
1) Root cause hypotheses ranked by likelihood.
2) Recommended fill strategy (backfill/source_expansion/inference/fallback_ux) with rationale.
3) Concrete validation rules and SQL/pseudocode checks.
4) Priority confirmation (P0/P1/P2) based on user impact.
5) A 1-week execution plan with dependencies.
Use concise tables.
```

## 3) Django Admin Data Loading Automation (Schema Upload + Upsert)

You already have a baseline importer:
- Admin endpoint: `SchoolAdmin.upload_csv`
- Importer: `apps/schools/csv_import.py`

Current constraint: fixed column names and upsert by `name` only.

### Target capability
Upload:
1. A dataset file (`.csv` initially).
2. A schema/mapping file (`.json` or `.yaml`) defining field map, types, keys, and validation.

Then run:
- `Dry run`: parse, validate, and report creates/updates/errors with no writes.
- `Commit`: perform transactional upsert with audit log.

### Recommended backend design

#### A. New models
- `ImportSchema`
  - `name`, `version`, `target_model` (e.g., `schools.School`)
  - `mapping_json` (source column -> model field)
  - `unique_key_fields` (e.g., `["nces_unitid"]` fallback `["name","state"]`)
  - `type_rules`, `required_fields`, `defaults`, `active`
- `DataLoadJob`
  - `schema` FK, `uploaded_file`, `status`, `dry_run`
  - `created_count`, `updated_count`, `error_count`
  - `report_file`, `started_at`, `finished_at`, `triggered_by`

#### B. Import service (new module)
- `apps/schools/import_pipeline.py` with functions:
  - `parse_rows(file)`
  - `apply_mapping(row, schema)`
  - `validate(mapped_row, schema)`
  - `resolve_upsert_key(mapped_row, schema)`
  - `execute_upsert(rows, schema, dry_run)`
- Return row-level outcomes for downloadable report.

#### C. Admin UX
- Add `DataLoadJobAdmin` with action buttons:
  - `Upload + Dry Run`
  - `Commit Last Dry Run`
  - `Download Error Report`
- Keep your existing `Upload CSV` for quick/manual usage during transition.

#### D. Safety controls
- Enforce dry-run before commit.
- Wrap commit in DB transaction.
- Row-level error isolation; continue processing other rows.
- Require explicit unique key declaration in schema.
- Add max-row threshold + confirmation for large imports.

#### E. First implementation scope (1 sprint)
1. Support CSV only.
2. Support `School` target model only.
3. Support JSON schema format only.
4. Upsert keys allowed: `nces_unitid` or `name+state`.
5. Export report CSV with per-row status and message.

## 4) Definition of Done for Data Gaps

A gap is `done` only when:
1. The gap register row is `closed`.
2. Validation rule passes in latest run.
3. Scorecard reflects target met for 2 consecutive weekly snapshots.
4. Import report is archived for audit.

## 5) Suggested next repo tasks

1. Create `ImportSchema` and `DataLoadJob` models + migrations.
2. Implement `import_pipeline.py` with dry-run first.
3. Add Django Admin pages/actions for schema upload and job execution.
4. Add tests for mapping, validation, and upsert key behavior.
