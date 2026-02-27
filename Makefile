.PHONY: setup up down status logs verify-staging-frontend deploy-staging-frontend

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
