# Torgstat SaaS Analytics Case

This repository is an analytics-engineering case study for a synthetic B2B subscription SaaS product. It models workspace ownership, user acquisition, subscription and plan history, invoice lifecycle, product events, multi-currency reporting, and controlled source-data defects.

The central command reference, operating tactics, quality gates, and project roadmap are maintained in [`PROJECT_PLAYBOOK.md`](PROJECT_PLAYBOOK.md). The layer-by-layer certification procedure and SQL-to-Power-BI reconciliation are documented in [`docs/validation_runbook.md`](docs/validation_runbook.md).

```text
Synthetic source extracts
        ↓
Validated CSV contracts
        ↓
PostgreSQL raw schema
        ↓
dbt staging views
        ↓
dbt dimensions, facts, and billing marts
        ↓
Power BI PBIP project: TMDL model and PBIR report
```

## Business Scenario

Torgstat is a fictional multi-tenant B2B SaaS analytics product. A customer is
represented by a workspace; users work inside it, subscriptions and invoices
belong to it, and product events describe its usage. Logical source domains
simulate an application database, subscription service, Billing/ERP, product
telemetry, and an external FX provider.

The analytics product exists to give Leadership and Finance one controlled view
of billing and customer scale, while letting Billing Operations and source
owners trace a data-quality problem to a concrete invoice, workspace, source
row, and load batch. The primary current financial measure is
`Eligible Paid Invoice Net USD (by issue date)`, technically still named
`Net Revenue USD`; it must not be presented as cash collection or accounting
recognized revenue.

The full project charter, stakeholder decisions, KPI framework, current scope,
and portfolio wording are in [`docs/business_case.md`](docs/business_case.md).
A self-contained introduction for a browser is available as
[`docs/business_case_report/torgstat_business_case.html`](docs/business_case_report/torgstat_business_case.html).

## Your Simulated Role

You work as the Analytics Engineer / BI Developer for Billing and Product
Analytics. A normal change starts with a ticket and metric definition, continues
through source/raw/staging/marts and tests, and finishes with DAX reconciliation,
Power BI UAT, Git review, and a release decision. You do not repair ERP data in
the report: you identify affected business IDs, route them to the source owner,
and verify the correction after the next load.

The practical eight-week work simulation, realistic tickets, acceptance
criteria, incidents, evidence, and release exercises are in
[`docs/training_program.md`](docs/training_program.md). Reusable work-item,
metric, incident, and release templates are in
[`docs/templates/`](docs/templates/).

## Delivery State

| State | Included |
| --- | --- |
| Current | Deterministic extracts, PostgreSQL raw load, dbt staging/marts/tests, multi-currency invoice conversion, Executive Overview, QA Revenue Trace, initial Data Quality Monitor, PBIP/TMDL/PBIR in Git |
| Next | Correct ambiguous DAX definitions, finish business breakdowns, add Acquisition/Usage and workspace drill-through, create an issue-grain DQ mart and CI gates |
| Later | Training managed PostgreSQL, environment separation, scheduled orchestration, monitoring, release/rollback evidence |
| Not claimed | Real customer data, production SLA/HA, enterprise ERP or card-processing integration, enterprise Power BI distribution |

## Technology Stack

- Python 3.11+, pandas, SQLAlchemy, and psycopg2
- PostgreSQL 15 in Docker Compose
- dbt Core 1.10 with the PostgreSQL adapter
- Bash database initialization and health checks
- Power BI for the reporting layer

## Repository Structure

```text
.
├── data/                         Generated CSV extracts and dataset documentation
├── docs/                         Business case, training, rules, contracts, runbooks, templates
├── init/                         PostgreSQL first-run initialization
├── report/                       Version-controlled Power BI PBIP project and blueprint
├── scripts/
│   ├── generate_data.py          Deterministic v1 dataset generator
│   ├── fetch_fx_rates.py         Historical FX-rate ingestion
│   ├── import_to_postgres.py     Validated raw-schema loader
│   ├── run_local_pipeline.sh     End-to-end local pipeline
│   ├── validate_end_to_end.sql    Cross-layer counts, formulas, and reconciliations
│   └── validate_power_bi_project.py  PBIP/TMDL structural checks
├── src/torgstat/                 Reusable Python package code
├── torgstat_dbt/                 dbt sources, staging, marts, tests, and macros
├── check_postgres.sh             Local database health checks
└── docker-compose.yml            PostgreSQL service
```

## Data Model

The deterministic generator uses seed `42` and creates eight core files. FX rates are refreshed separately.

| Dataset | Rows | Grain |
| --- | ---: | --- |
| `workspaces` | 200 | One current workspace |
| `plans` | 4 | One product plan |
| `users` | 2,500 | One current user |
| `sessions` | 1,297 | One user session |
| `subscriptions` | 180 | One stable subscription lifecycle |
| `subscription_plan_history` | 234 | One plan period for a subscription |
| `invoices` | 935 | One billing-period invoice |
| `events` | 5,000 | One workspace event occurrence |
| `fx_rates` | Refreshed separately | One daily currency-pair rate |

```text
workspaces 1 ─── * users 1 ─── * sessions
     │
     ├── * subscriptions 1 ─── * subscription_plan_history * ─── 1 plans
     │            └── * invoices ──────────────────────────────── 1 plans
     └── * events
```

Every workspace has an owner record, and every active workspace has exactly one active owner. A workspace may exist without a subscription. Plan upgrades and downgrades preserve `subscription_id` and create a new non-overlapping history period.

The approved field-level contracts and business decisions are documented in `docs/data_contract.md` and `docs/business_rules.md`.

## Quick Start

For the normal Mac + Windows VM operating sequence, connection checks, pipeline commands, and Power BI startup, use [`docs/daily_runbook.md`](docs/daily_runbook.md).

### 1. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure the environment

Copy `.env.example` to `.env` and set PostgreSQL, schema, application-user, and read-only-user credentials.

```bash
cp .env.example .env
```

Do not commit `.env`.

`dbt` reads variables from the process environment, not directly from `.env`. The
`set -a` / `set +a` pair below exports every sourced value to child processes.

### Run the complete local pipeline

```bash
./scripts/run_local_pipeline.sh
```

After FX rates have already been downloaded, a faster repeat is available:

```bash
./scripts/run_local_pipeline.sh --skip-fx
```

### 3. Start PostgreSQL

```bash
docker compose up -d
./check_postgres.sh
```

The official image runs `init/init.sh` only for an empty `postgres_data/` directory. See `init/README.md` before resetting an existing local database.

### 4. Generate source files

```bash
python scripts/generate_data.py
```

The generator validates global identifiers, workspace ownership, first-session rules, and plan-period integrity before writing CSV files.

Refresh FX rates when network access is available:

```bash
python scripts/fetch_fx_rates.py
```

### 5. Load raw tables

```bash
python scripts/import_to_postgres.py
```

The importer requires all contracted files, validates exact column order, adds load lineage, and replaces each raw table. Replacement uses `DROP TABLE ... CASCADE`, so dbt relations must be rebuilt after a load.

### 6. Build dbt models

```bash
set -a
source .env
set +a
.venv/bin/python -m dbt.cli.main build \
  --project-dir torgstat_dbt \
  --profiles-dir torgstat_dbt
```

Generate lineage and model documentation with:

```bash
.venv/bin/python -m dbt.cli.main docs generate \
  --project-dir torgstat_dbt \
  --profiles-dir torgstat_dbt
```

## dbt Layers

The project defines nine raw sources, nine staging views, and eleven marts models.

Staging performs typing, normalization, source-lineage propagation, and explicit quality flags. Important controls include invalid user timestamps, lifecycle consistency, invoice amount reconciliation, payment lifecycle, first-touch attribution, and plan-period validity.

Marts contain:

- `dim_date`, `dim_workspaces`, `dim_users`, and `dim_plans`;
- `fct_subscriptions` and `fct_subscription_plan_history`;
- `fct_invoices` and `fct_invoices_converted`;
- `fct_sessions` and `fct_events`;
- `mart_workspace_monthly_billing`.

Power BI reporting starts from the PBIP project in `report/power_bi/`. The semantic model, relationships, Power Query partitions, and DAX measures are stored as TMDL. Power BI Desktop writes pages and visuals as PBIR JSON files, which are committed to Git while local caches remain ignored.

Singular dbt tests enforce workspace owner integrity, session temporal consistency, exactly one earliest first session, UTM placement, non-overlapping subscription and plan periods, invoice snapshots, structural invoice quality, and the absence of Free-plan invoices.

## Controlled Data Quality

The generator intentionally creates small, documented defect populations:

- 1% invalid raw user creation timestamps;
- approximately 2% missing user countries;
- missing first-touch source values for invited users and a small source-loss scenario;
- approximately 2% missing invoice currencies;
- approximately 1% invoice amount reconciliation mismatches;
- approximately 3% failed invoice payments.

Accidental identifier collisions, negative invoice amounts, random first-session flags, and sessions before user creation are not generated in v1.

## Current Limitations

- The current PBIP release contains an initial Executive Overview, QA Revenue Trace, and Data Quality Monitor. Revenue/Plans, Acquisition/Usage, workspace drill-through, and a production remediation workflow remain documented roadmap items.
- Raw loading replaces tables instead of preserving append-only batch history.
- Invoice-currency fallback to workspace default and the authoritative FX conversion date remain separate draft business decisions.
- Recognized-revenue, MRR, and ARR marts are not implemented yet.
- Runtime `dbt build` requires a running PostgreSQL instance; static parsing can run without Docker.

Changes must follow `docs/change_workflow.md`: business rule → contract → generator → importer → source → staging → marts → tests → docs → visualization.
