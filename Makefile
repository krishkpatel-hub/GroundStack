.PHONY: setup dev test lint format typecheck db-up db-down migrate migration-check predeploy seed-demo api-dev web-dev eval-retrieval benchmark-retrieval validate-training-data prepare-training-data training-preflight train-qlora compare-models training-test review-training-candidates export-approved-training-data eval eval-generation eval-security compare-prompts load-smoke-fake load-sustained-fake load-300-real

setup:
	npm install
	cd apps/api && python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"

dev:
	$(MAKE) db-up
	$(MAKE) migrate
	$(MAKE) -j2 api-dev web-dev

api-dev:
	cd apps/api && . .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

web-dev:
	npm run dev --workspace apps/web

test:
	cd apps/api && . .venv/bin/activate && pytest

lint:
	cd apps/api && . .venv/bin/activate && ruff check .
	npm run lint --workspace apps/web
	npm run typecheck --workspace apps/web

typecheck:
	cd apps/api && . .venv/bin/activate && python -m compileall -q app
	npm run typecheck --workspace apps/web

format:
	cd apps/api && . .venv/bin/activate && ruff format .
	npm run format --workspace apps/web

db-up:
	docker compose up -d postgres

db-down:
	docker compose down

migrate:
	cd apps/api && . .venv/bin/activate && alembic upgrade head

migration-check:
	cd apps/api && . .venv/bin/activate && cd ../.. && python scripts/check_migrations.py

predeploy:
	cd apps/api && . .venv/bin/activate && cd ../.. && python scripts/predeploy.py

seed-demo:
	cd apps/api && . .venv/bin/activate && cd ../.. && PYTHONPATH=apps/api python scripts/seed_demo.py

ingest:
	cd apps/api && . .venv/bin/activate && python -m app.cli.ingest "$(FILE)"

ingest-sample:
	cd apps/api && . .venv/bin/activate && python -m app.cli.ingest dev-data/knowledge-base

eval-retrieval:
	cd apps/api && . .venv/bin/activate && python -m app.cli.eval_retrieval

benchmark-retrieval:
	cd apps/api && . .venv/bin/activate && python -m app.cli.benchmark_retrieval

validate-training-data:
	PYTHONPATH=training python3 training/scripts/validate_dataset.py

prepare-training-data:
	PYTHONPATH=training python3 training/scripts/prepare_dataset.py --config $(or $(CONFIG),training/configs/smoke_test.yaml)

training-preflight:
	PYTHONPATH=training python3 training/scripts/preflight.py --config $(or $(CONFIG),training/configs/llama32_3b_qlora.yaml)

train-qlora:
	PYTHONPATH=training python3 training/scripts/train_sft.py --config $(or $(CONFIG),training/configs/llama32_3b_qlora.yaml)

compare-models:
	PYTHONPATH=training python3 training/scripts/compare_models.py $(if $(BASE_RESPONSES),--base-responses $(BASE_RESPONSES),) $(if $(ADAPTER_RESPONSES),--adapter-responses $(ADAPTER_RESPONSES),)

training-test:
	cd training && PYTHONPATH=. ../apps/api/.venv/bin/python -m pytest

review-training-candidates:
	cd apps/api && . .venv/bin/activate && python -m app.cli.review_training_candidates list

export-approved-training-data:
	cd apps/api && . .venv/bin/activate && python -m app.cli.export_approved_training_data --output ../../training/data/processed/approved_feedback.jsonl

eval:
	PYTHONPATH=evaluation python3 evaluation/runners/run_eval.py --suite all

eval-generation:
	PYTHONPATH=evaluation python3 evaluation/runners/run_eval.py --suite generation

eval-security:
	PYTHONPATH=evaluation python3 evaluation/runners/run_eval.py --suite prompt_injection --suite security

compare-prompts:
	PYTHONPATH=evaluation python3 evaluation/runners/compare_prompts.py

load-smoke-fake:
	cd apps/api && . .venv/bin/activate && cd ../.. && python -m load.run_locust_profile --profile fake-smoke

load-sustained-fake:
	cd apps/api && . .venv/bin/activate && cd ../.. && python -m load.run_locust_profile --profile fake-sustained

load-300-real:
	cd apps/api && . .venv/bin/activate && cd ../.. && python -m load.run_locust_profile --profile real-300 --require-real
