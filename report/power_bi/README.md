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

The semantic model and a blank Executive Overview page are already authored as code. Power BI Desktop adds one PBIR JSON file per visual as the report is built. Commit those files to Git.

## Scope

The first report should answer four business questions:

- How much eligible revenue did the SaaS product bill over time?
- Which plans, countries, segments, and acquisition sources drive revenue?
- Are subscriptions, sessions, and product events moving in the same direction?
- Which controlled data-quality issues affect reporting trust?

## Local Data Connection

TMDL parameters default to `Server = localhost:5433` and `Database = torgdb`. Credentials are intentionally absent from Git and are stored by Power BI Desktop for the current user.

If PostgreSQL runs on the Mac host while Power BI Desktop runs inside a Windows VM, do not use `localhost`: inside Windows it refers to the VM. Set the Power BI `Server` parameter to `<mac-ip>:5433`, keep `Database = torgdb`, and authenticate with `READONLY_USER` and `READONLY_PASSWORD` from the Mac `.env` file.

Check connectivity before opening the project:

```powershell
Test-NetConnection <mac-ip> -Port 5433
```

The test must return `TcpTestSucceeded : True`. Docker, the local pipeline, and PostgreSQL remain on the Mac; only Power BI Desktop and a Git working copy are required in Windows.

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
6. Build the pages from `report_blueprint.md` and save the project.
7. Review `git diff`, then commit the generated PBIR files.

Power BI Desktop must be restarted after external TMDL or PBIR edits because it does not hot-reload project files.

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

## Refresh Order

1. Run `./scripts/run_local_pipeline.sh`.
2. Open or restart the PBIP project.
3. Refresh the Power BI semantic model.
4. Review changes before committing them.

Validate the source-controlled project structure at any time:

```bash
.venv/bin/python scripts/validate_power_bi_project.py
```
