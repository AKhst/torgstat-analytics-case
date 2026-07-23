# Power BI As Code

This folder contains a Power BI Project (`PBIP`) instead of a binary `.pbix`. The semantic model is stored as TMDL files, one file per table, while Power BI Desktop stores report pages and visuals as PBIR JSON files. These formats are readable, diffable, and reviewable in Git.

## Project Structure

```text
TorgstatAnalytics.pbip
TorgstatAnalytics.SemanticModel/
├── definition.pbism
└── definition/
    ├── database.tmdl
    ├── expressions.tmdl
    ├── model.tmdl
    ├── relationships.tmdl
    └── tables/*.tmdl
TorgstatAnalytics.Report/
├── definition.pbir
└── definition/
    ├── report.json
    ├── version.json
    └── pages/
        ├── pages.json
        └── ExecutiveOverview/page.json
```

The semantic model and report are authored as code. Power BI Desktop adds one PBIR JSON file per visual as the report is built. Commit those files to Git.

## Current Authoring State

The report currently contains:

- `Executive Overview`: an invoice-date slicer, five KPI cards, and a monthly net-revenue line chart;
- `QA Revenue Trace`: an invoice-level table for reconciling the revenue measure to its source rows;
- `Data Quality Monitor`: five quality KPI cards, a customer-segment slicer, monthly invoice-mismatch trend, and invoice/user detail tables with business IDs and quality flags.

The Executive Overview KPI strip uses `Net Revenue USD`, `Gross Revenue USD`, `Paid Invoices`, `Payment Success Rate`, and `Active Paid Workspaces`. The first four metrics are filtered by the active invoice-date relationship. `Active Paid Workspaces` is a current full-data subscription metric and does not respond to the invoice-date slicer.

The next planned report work is:

1. Complete the Executive Overview breakdowns by plan, customer segment, and country.
2. Add `Revenue And Plans` and `Acquisition And Usage` pages.
3. Add the workspace drill-through page.
4. Evolve the initial Data Quality Monitor into an operational workflow backed by a dedicated `mart_data_quality_issues` model.

`report_blueprint.md` contains the target page layout. `semantic_model.md` documents table grain, relationships, and date behavior.

## Scope

The first report should answer four business questions:

- How much eligible revenue did the SaaS product bill over time?
- Which plans, countries, segments, and acquisition sources drive revenue?
- Are subscriptions, sessions, and product events moving in the same direction?
- Which controlled data-quality issues affect reporting trust?

## Local Data Connection

TMDL parameters default to `Server = localhost:5433` and `Database = torgdb`. Credentials are intentionally absent from Git and are stored by Power BI Desktop for the current user.

If PostgreSQL runs on the Mac host while Power BI Desktop runs inside a Windows VM, do not use `localhost`: inside Windows it refers to the VM. Set the Power BI `Server` parameter to `MacBook-Pro-Aleksei.local:5433` (or another approved DNS hostname), keep `Database = torgdb`, and authenticate with `READONLY_USER` and `READONLY_PASSWORD` from the Mac `.env` file.

Check connectivity before opening the project:

```powershell
Test-NetConnection MacBook-Pro-Aleksei.local -Port 5433
```

The test must return `TcpTestSucceeded : True`. Docker, the local pipeline, and PostgreSQL remain on the Mac; only Power BI Desktop and a Git working copy are required in Windows.

The day-to-day startup and troubleshooting sequence is documented in [`../../docs/daily_runbook.md`](../../docs/daily_runbook.md).

There are two supported ways to obtain data after cloning the repository:

1. **Shared database:** open the PBIP, change `Server` and `Database`, enter the read-only credentials, and refresh. No local Python, Docker, data generation, import, or dbt run is required.
2. **Independent local database:** configure `.env`, run the complete local pipeline, connect the PBIP to `localhost:5433`, and refresh.

Git transports the report and model definitions, not imported data or credentials. A cloned report therefore has its pages, visuals, measures, and relationships, but requires a reachable PostgreSQL database before its visuals can display refreshed data.

Recommended import tables:

- `dim_date`
- `dim_workspaces`
- `dim_users`
- `dim_plans`
- `fct_subscriptions`
- `fct_subscription_plan_history`
- `fct_invoices_converted`
- `fct_sessions`
- `fct_events`
- `mart_workspace_monthly_billing`

Avoid importing raw and staging tables into the first report. They are useful for engineering validation, but the report should be built on stable marts.

## First Desktop Open

1. Run the local pipeline and confirm `dbt build` succeeds.
2. In Power BI Desktop, enable the PBIP, TMDL, and PBIR preview features.
3. Open `TorgstatAnalytics.pbip`.
4. Enter the local PostgreSQL read-only credentials when prompted.
5. Apply changes and refresh the model.
6. Review the implemented pages against `report_blueprint.md`, make the intended report changes, and save the project.
7. Review `git diff`, then commit the generated PBIR files.

Power BI Desktop must be restarted after external TMDL or PBIR edits because it does not hot-reload project files.

## BI-As-Code File Map

- `TorgstatAnalytics.pbip` is the project entry point.
- `TorgstatAnalytics.Report/definition/pages/**/page.json` defines report pages.
- `TorgstatAnalytics.Report/definition/pages/**/visuals/**/visual.json` defines visual type, field bindings, layout, filters, and formatting.
- `TorgstatAnalytics.SemanticModel/definition/tables/*.tmdl` defines tables, columns, partitions, and DAX measures.
- `TorgstatAnalytics.SemanticModel/definition/relationships.tmdl` defines model relationships.
- `TorgstatAnalytics.SemanticModel/definition/expressions.tmdl` defines the `Server` and `Database` parameters, but never credentials.

Power BI Desktop may normalize or rewrite many TMDL files on its first save. Review that generated diff separately from later business changes. Do not hand-edit PBIR or TMDL while Power BI Desktop has the project open because the application can overwrite external changes.

## Understanding Date Relationships

Invoice issue date is the active reporting date. Session, event, and monthly-billing date relationships are inactive and are activated only by measures such as `Sessions By Session Date` and `Events By Event Date` through `USERELATIONSHIP()`.

For a quick learning check, create a temporary page with a `dim_date[date_day]` slicer and compare `Sessions` with `Sessions By Session Date`, then `Events` with `Events By Event Date`. Only the date-aware measures should change when the date range changes.

Use `dim_date` as the shared reporting calendar. Avoid building production visuals on Power BI's automatically generated local date tables.

## Data Quality Handoff

The initial Data Quality page uses the existing measures for missing invoice currency, invoice amount mismatch, invalid user timestamps, missing user country, and FX coverage. Its record-level invoice and user tables include business IDs and quality flags so an issue can be traced back through marts, staging, raw tables, and the source extract. Use the table flags to isolate affected records; `loaded_at_utc` remains available in the semantic model for load-level lineage.

An operational remediation workflow needs more than visual counts. Before handing issues to ERP or source-system owners, add a durable issue-grain model with issue code, entity and record ID, source system, field, severity, detected timestamp, batch lineage, owner team, resolution status, and ticket ID. Power BI should monitor and route the issue; the source record should be corrected in ERP and verified by a subsequent pipeline run.

## Windows VM Git Workflow

Clone once in PowerShell:

```powershell
git clone https://github.com/AKhst/torgstat-analytics-case.git
cd torgstat-analytics-case
```

Before receiving changes, close Power BI Desktop and run `git pull --ff-only`. After editing and saving the report, review `git status` and `git diff`, commit only intentional PBIR/TMDL changes, and push them. Never use Git as a database transport: the Windows project connects to the running PostgreSQL instance and Git transports only report/model source code.

## Git Rules

Commit:

- `.pbip`, `.pbir`, `.pbism`, `.tmdl`, and PBIR `.json` definitions;
- report themes and intentional static resources;
- semantic-model and report documentation.

Do not commit:

- `.pbix` binaries;
- `.pbi/cache.abf` data caches;
- `.pbi/localSettings.json` machine-specific settings;
- `.env` or database credentials.

Before committing, check `expressions.tmdl`. Replace a personal or temporary LAN IP with the agreed default (`localhost:5433` for this repository) or an approved shared DNS name. Database passwords are stored outside the project and must never appear in the diff.

## Refresh Order

1. Run `./scripts/run_local_pipeline.sh`.
2. Open or restart the PBIP project.
3. Refresh the Power BI semantic model.
4. Review changes before committing them.

Validate the source-controlled project structure at any time:

```bash
python -m unittest discover -s tests -p "test_validate_power_bi_project.py"
python scripts/validate_power_bi_project.py
```

The validator scopes `formatString` checks to individual measure blocks. This is intentional: Power BI also serializes `formatString` for date and numeric columns, so counting every occurrence in a table file would incorrectly report valid column formatting as missing measure formatting. Keep the regression tests whenever the TMDL parser changes.
