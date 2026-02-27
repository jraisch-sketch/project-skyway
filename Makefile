.PHONY: setup up down status logs verify-staging-frontend deploy-staging-frontend snapshot-to-staging snapshot-to-local snapshot-only list-snapshots

setup:
	./dev setup

up:
	./dev up

down:
	./dev down

status:
	./dev status

logs:
	./dev logs

verify-staging-frontend:
	./scripts/verify_staging_frontend.sh

deploy-staging-frontend:
	./scripts/deploy_staging_frontend.sh

snapshot-only:
	./scripts/db_snapshot_sync.sh snapshot-only

snapshot-to-staging:
	./scripts/db_snapshot_sync.sh snapshot-to-staging --yes

snapshot-to-local:
	./scripts/db_snapshot_sync.sh snapshot-to-local --yes

list-snapshots:
	./scripts/db_snapshot_sync.sh list-snapshots
