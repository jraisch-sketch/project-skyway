# DB Snapshot Sync Plan (Prod -> Staging/Local)

## Goal

Provide a simple, repeatable way to:
- snapshot production data
- restore that snapshot to staging
- restore that snapshot to local

Without redoing manual `pg_dump`/`pg_restore` steps each time.

## Commands

From repo root:

```bash
make snapshot-to-staging
make snapshot-to-local
make snapshot-only
make list-snapshots
```

Underlying script:

```bash
./scripts/db_snapshot_sync.sh <command>
```

## Configuration

1. Copy env template:

```bash
cp scripts/db_sync.env.example scripts/db_sync.env
```

2. Fill credentials for:
- production source DB (`PROD_DB_*`)
- staging target DB (`STAGING_DB_*`)
- local target DB (`LOCAL_DB_*`) optional if `backend/.env` already has `POSTGRES_*`

`scripts/db_sync.env` is ignored by git.

## Safety Guardrails

- Restore commands are destructive to target DB contents.
- `make` shortcuts use `--yes` for fast execution; direct script usage prompts by default.
- Script always snapshots prod first for `snapshot-to-staging` and `snapshot-to-local`.
- Snapshot artifacts are stored in `snapshots/db/*.dump`.

## Current Implementation Notes

- Snapshot format: PostgreSQL custom dump (`pg_dump --format=custom`).
- Restore mode: `pg_restore --clean --if-exists --single-transaction`.
- This is data-level cloning (fast and explicit), not RDS instance snapshot restore orchestration.

## Next Hardening (Optional)

- Add post-restore validation checks:
  - expected row counts on key tables
  - schema version check
- Add PII scrub step for staging/local after restore.
- Add date-stamped retention cleanup (`keep last N snapshots`).
- Add read-only lock/maintenance-mode hooks around staging restore windows.
