#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ ! -f .env ]]; then
  echo "Missing .env. Create it with: cp .env.example .env" >&2
  exit 1
fi

if [[ ! -x .venv/bin/python ]]; then
  echo "Missing .venv. Create it and install requirements first." >&2
  exit 1
fi

set -a
source .env
set +a

docker compose up -d
./check_postgres.sh

.venv/bin/python scripts/generate_data.py

if [[ "${1:-}" == "--skip-fx" ]]; then
  if [[ ! -f data/fx_rates.csv ]]; then
    echo "data/fx_rates.csv is missing; rerun without --skip-fx." >&2
    exit 1
  fi
else
  .venv/bin/python scripts/fetch_fx_rates.py
fi

.venv/bin/python scripts/import_to_postgres.py
.venv/bin/python -m dbt.cli.main source freshness \
  --project-dir torgstat_dbt \
  --profiles-dir torgstat_dbt
.venv/bin/python -m dbt.cli.main build \
  --project-dir torgstat_dbt \
  --profiles-dir torgstat_dbt

docker compose exec -T postgres \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -v raw_schema="$RAW_SCHEMA" \
  -v staging_schema="$STAGING_SCHEMA" \
  -v marts_schema="$MARTS_SCHEMA" \
  < scripts/validate_end_to_end.sql

.venv/bin/python scripts/validate_power_bi_project.py
