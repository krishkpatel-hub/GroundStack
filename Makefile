.PHONY: setup dev api-dev web-dev test lint typecheck format db-up db-down migrate migration-check predeploy deploy-check migrate-production db-smoke ingest

setup:
	npm install
	cd apps/api && python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"

dev: db-up migrate
	$(MAKE) -j2 api-dev web-dev

api-dev:
	cd apps/api && . .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

web-dev:
	npm run dev --workspace apps/web

test:
	cd apps/api && . .venv/bin/activate && pytest
	npm run test --workspace apps/web

lint:
	cd apps/api && . .venv/bin/activate && ruff format --check . && ruff check .
	npm run lint --workspace apps/web

typecheck:
	cd apps/api && . .venv/bin/activate && python -m compileall -q app
	npm run typecheck --workspace apps/web

format:
	cd apps/api && . .venv/bin/activate && ruff format .
	npm run format --workspace apps/web

db-up:
	docker compose up -d --wait postgres

db-down:
	docker compose down

migrate:
	cd apps/api && . .venv/bin/activate && alembic upgrade head

migration-check:
	cd apps/api && . .venv/bin/activate && cd ../.. && python scripts/check_migrations.py

predeploy:
	cd apps/api && . .venv/bin/activate && cd ../.. && python scripts/predeploy.py

deploy-check:
	cd apps/api && . .venv/bin/activate && cd ../.. && PYTHONPATH=apps/api python scripts/deploy_check.py

migrate-production:
	cd apps/api && . .venv/bin/activate && cd ../.. && PYTHONPATH=apps/api python scripts/migrate_production.py

db-smoke:
	cd apps/api && . .venv/bin/activate && cd ../.. && PYTHONPATH=apps/api python scripts/db_smoke.py

ingest:
	cd apps/api && . .venv/bin/activate && python -m app.cli.ingest "$(FILE)"
