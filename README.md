# Torgstat SaaS Analytics Case

This repository is a work-in-progress analytics engineering case study for a synthetic B2B subscription SaaS product. It currently implements local data generation, loading into PostgreSQL, and a tested dbt staging layer.

The intended data flow is:

```text
Synthetic ERP/billing data -> CSV files -> PostgreSQL raw schema -> dbt staging -> marts -> BI reports
```

The CSV generation, PostgreSQL raw load, and six dbt staging views are implemented. Mart models and Power BI artifacts have not been added yet.

## Technology Stack

- PostgreSQL 15 in Docker Compose
- Python, pandas, SQLAlchemy, and psycopg2
- dbt Core with the PostgreSQL adapter
- Bash scripts for database initialization and health checks
- Power BI is planned for the reporting layer

## Repository Structure

```text
.
├── data/                         Generated CSV files and dataset documentation
├── init/                         PostgreSQL first-run initialization
├── report/                       Placeholder for future report artifacts
├── scripts/
│   ├── generate_data.py          Generates the synthetic SaaS dataset
│   └── import_to_postgres.py     Replaces tables in the raw schema
├── src/torgstat/                 Reusable Python package code
├── torgstat_dbt/
│   ├── dbt_project.yml           dbt project configuration
│   └── models/                   Sources and current staging models
├── check_postgres.sh             Checks the container, schemas, and roles
├── docker-compose.yml            Local PostgreSQL service
├── requirements.txt              Python and dbt dependencies
└── setup.py                      Local package metadata
```

## Implemented Data Model

The generator creates six CSV files:

| Dataset | Typical row count | Main relationship |
| --- | ---: | --- |
| `plans` | 4 | Referenced by subscriptions and invoices |
| `users` | 2,500 | Belongs to a workspace |
| `sessions` | 1,000 | References a user |
| `subscriptions` | 200 | Belongs to a workspace and plan |
| `invoices` | About 2,280 | References a subscription, workspace, and plan |
| `events` | 5,000 | Belongs to a workspace |

Generation is deterministic because both Python and NumPy use seed `42`. See [data/README.md](data/README.md) for the exact columns and injected data-quality issues.

PostgreSQL uses three schemas configured through environment variables:

- `raw`: tables loaded directly from CSV files
- `staging`: intended for cleaned and typed dbt views
- `marts`: intended for BI-ready fact and dimension tables

The `raw` and `staging` layers are implemented. The marts layer is planned.

## Quick Start

### 1. Install prerequisites

You need:

- Python 3.11 or later
- Docker with Docker Compose
- `nc` (netcat) for `check_postgres.sh`

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure the environment

Create `.env` in the repository root. All values below are required by the current Docker and initialization configuration:

```dotenv
POSTGRES_DB=torgdb
POSTGRES_USER=torgadmin
POSTGRES_PASSWORD=change_admin_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_SCHEMA=raw

RAW_SCHEMA=raw
STAGING_SCHEMA=staging
MARTS_SCHEMA=marts

APP_DB_USER=appuser
APP_DB_PASSWORD=change_app_password

READONLY_USER=readonly
READONLY_PASSWORD=change_readonly_password

PYTHONPATH=src
```

Use simple PostgreSQL identifiers for database, schema, and role names. Do not commit `.env`.

### 3. Start PostgreSQL

```bash
docker compose up -d
./check_postgres.sh
```

The official PostgreSQL image runs `init/init.sh` only when `postgres_data/` is empty. If that directory already contains a database, restarting the container does not rerun initialization or apply changed environment variables. See [init/README.md](init/README.md) for reset and troubleshooting instructions.

### 4. Generate the CSV files

```bash
python scripts/generate_data.py
```

This writes `plans.csv`, `users.csv`, `sessions.csv`, `subscriptions.csv`, `invoices.csv`, and `events.csv` to `data/`.

### 5. Load the raw schema

```bash
python scripts/import_to_postgres.py
```

The importer connects as `APP_DB_USER`. For every available CSV file, it drops the corresponding `raw` table with `CASCADE` and recreates it from the DataFrame. Rerunning the import therefore removes dependent dbt views.

Inspect the loaded tables with:

```bash
docker exec -it torgstat_postgres \
  psql -U torgadmin -d torgdb \
  -c "SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema = 'raw' ORDER BY table_name;"
```

## dbt Status

The dbt project is located in `torgstat_dbt/` and references all six tables in `raw`. Its workspace-centric staging layer contains:

- `stg_plans`: typed plan attributes and billing-period validation;
- `stg_users`: user-to-workspace membership, safe signup-date parsing, GDPR/deletion fields, and quality flags;
- `stg_sessions`: typed acquisition sessions and normalized UTM fields;
- `stg_subscriptions`: workspace subscriptions with normalized status and duplicate-ID flags;
- `stg_invoices`: workspace invoices with duplicate, currency, amount, and billing-period quality flags;
- `stg_events`: normalized workspace-level product events.

The project includes an environment-based `profiles.yml` and a schema naming macro, so staging models are created directly in the configured `STAGING_SCHEMA`.

Run all models and tests from the repository root:

```bash
set -a
source .env
set +a
dbt build --project-dir torgstat_dbt --profiles-dir torgstat_dbt
```

If the `dbt` executable resolves to dbt Fusion, which does not currently enable PostgreSQL by default, invoke the dbt Core installation from the virtual environment:

```bash
set -a
source .env
set +a
.venv/bin/python -m dbt.cli.main build \
  --project-dir torgstat_dbt \
  --profiles-dir torgstat_dbt
```

Known limitations:

- duplicate source subscription and invoice identifiers are retained and flagged, not silently removed;
- events do not have a source event identifier;
- there is no dedicated workspace source table, so workspace dimensions must be derived in marts;
- marts models and business-level metrics are not implemented yet.

## Reporting Status

The `report/` directory is a placeholder. There is currently no `.pbip`, Power BI semantic model, PDF, or presentation in the repository. The intended BI account is `READONLY_USER`, restricted to the marts schema, but permissions for future tables must be granted after those tables are created.

## Troubleshooting

- **Schemas are missing:** check `docker logs torgstat_postgres`. Confirm that all schema variables exist in `.env` and that `postgres_data/` was empty on first startup.
- **Initialization changes have no effect:** stop PostgreSQL and initialize a fresh data directory; entrypoint scripts never rerun against an existing cluster.
- **Raw import cannot connect:** confirm `POSTGRES_HOST=localhost`, the published `POSTGRES_PORT`, and the `APP_DB_USER` credentials.
- **dbt cannot connect:** activate the virtual environment, load `.env`, and confirm PostgreSQL is reachable on `POSTGRES_HOST:POSTGRES_PORT`.
- **BI user cannot read new marts tables:** grant access after model creation or configure PostgreSQL default privileges as described in `init/README.md`.
