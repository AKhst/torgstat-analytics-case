# Summary — SaaS Analytics Case v1

## Current Handoff Status — 2026-08-04

- Current branch: `fix/pbi-core-metrics`.
- Branch base: merged documentation PR #1 at `0f83012`.
- At the start of this documentation update the working tree was clean.
- The Windows Power BI Server parameter uses the developer's local Mac DNS
  hostname only in the local `expressions.tmdl`.
- `expressions.tmdl` is marked `skip-worktree` on Windows, so the personal Mac
  hostname is not pending for commit and is not transferred to other machines.
- Git is the approved transport between Mac and Windows; project decisions,
  SQL, TMDL, PBIR, documentation and validation evidence must not be copied
  manually between machines.

## Completed

- Business case, training workflow, report blueprint, runbooks and HTML project
  description were committed in `b153211` and merged through PR #1.
- The PBIP contains three source-controlled pages:
  `Executive Overview`, `QA Revenue Trace` and `Data Quality Monitor`.
- `Executive Overview` has the initial KPI strip, invoice-date slicer and
  monthly revenue trend.
- `QA Revenue Trace` provides invoice-level inspection.
- `Data Quality Monitor` has five DQ cards, customer segment slicer, mismatch
  trend and invoice/user detail tables.
- Static audit confirmed the semantic issues and filter-context gap listed
  below. No live PostgreSQL ↔ Power BI values were certified by that static
  audit.
- A clean feature branch `fix/pbi-core-metrics` was created for the next
  controlled change set.
- On Mac, `./scripts/run_local_pipeline.sh --skip-fx` refreshed the stale raw
  batch and completed with `PASS=427`, SQL audit `PASS` and a valid static PBIP
  structure.
- Mac SQL evidence, control slices and source-row traces for eligible invoice
  `10001` and mismatch invoice `10062` are recorded in
  `docs/evidence/QA-103_core_metrics_certification.md`.
- The approved `Canceled Subscriptions` predicate was corrected from `canceled`
  to the contract value `cancelled`. Runtime DAX and visual confirmation remain
  pending in Windows.

## Approved Current Scope

The current branch is limited to reviewable core-metric and DQ certification
work:

1. Correct `Canceled Subscriptions` from source value `canceled` to the approved
   contract value `cancelled`.
2. Add a visual-level
   `has_amount_reconciliation_mismatch = TRUE` filter to the invoice mismatch
   detail, include the required business fields and verify visual interactions.
3. Document the exact current meaning of `Net Revenue USD` as
   `Eligible Paid Invoice Net USD (by issue date)`.
4. Document, but do not invent, the unresolved definitions for billed amount,
   open receivable, cash collected and recognized revenue.
5. Document that the current `Active Paid Workspaces` counts active subscription
   workspaces but does not prove a non-Free plan or historical as-of state.
6. Reconcile PostgreSQL → dbt mart → DAX → Power BI visual and trace at least one
   valid invoice and one DQ invoice to staging/raw source metadata.
7. Save validation evidence and review the staged diff before each commit.

## Confirmed Findings

### Canceled Subscriptions

The current DAX filters `canceled`, while staging and the approved data contract
use `cancelled`. This is an unambiguous bug and does not require a new business
decision.

### Revenue Measures

`analytics_net_amount_usd` is populated only for analytics-eligible paid
invoices. Therefore:

- current `Net Revenue USD` means eligible paid invoice net amount converted to
  USD and grouped by invoice `issued_at`;
- `Paid Net Revenue USD` duplicates the same population;
- `Open Net Revenue USD` is structurally blank because non-paid invoices do not
  have `analytics_net_amount_usd`;
- the current measure is not cash collection by `paid_at` and is not accounting
  recognized revenue.

No replacement billed/open/cash/recognized-revenue implementation is approved
yet.

### Active Paid Workspaces

The current measures count subscription workspaces and active subscription
workspaces. They do not join to a current non-Free plan and do not implement an
historical as-of rule. The repository has plan history but no complete
subscription-status history.

The choice between a current snapshot, a selected-date as-of metric and
workspaces with paid invoices in a period remains a metric/data-contract
decision. No historical implementation is approved yet.

### Data Quality Drill-Down

The internal TRUE predicate in `Invoice Amount Mismatch Count` affects only the
measure calculation. Clicking the monthly line chart passes the month to the
detail table, not the measure's internal mismatch predicate. The current invoice
detail PBIR has no visual-level filter, so it can show all invoices in the
selected month.

The approved short-term fix is an explicit visual filter
`has_amount_reconciliation_mismatch = TRUE` plus tested chart-to-table
interaction. The production `mart_data_quality_issues` remains a separate future
feature.

## Next Step

1. Review the Mac diff and static validation output.
2. Commit and push the Mac checkpoint to `fix/pbi-core-metrics`.
3. In Windows close Power BI Desktop, pull the branch and refresh the model.
4. Confirm `Canceled Subscriptions = 36` in DAX Query View and the report.
5. Reconcile no-filter and control-slice DAX/visual values against
   `docs/evidence/QA-103_core_metrics_certification.md`.
6. Add the approved invoice mismatch visual-level `TRUE` filter and verify
   chart-to-detail interactions in Power BI Desktop.
7. Update the evidence with Windows UAT results, review the PBIP/PBIR diff, then
   commit and push only the intended changes.

## Current Blockers and Unapproved Decisions

- Billed amount, open receivable, cash collected and recognized revenue have no
  approved separate definitions or implementation.
- Historical `Active Paid Workspaces as of selected date` requires an approved
  as-of rule and adequate status history or snapshot design.
- Invoice currency fallback and authoritative FX date remain draft business
  rules.
- Mac SQL totals and record-level trace evidence are recorded, but live DAX and
  Power BI visual reconciliation is still pending in Windows.
- Dashboard MVP is not complete: Executive Overview and Data Quality Monitor are
  partial, and the planned Revenue and Plans, Acquisition and Usage, and
  Workspace Drill-Through pages are not implemented.

## Cross-Machine Working Rule

Use one feature branch as the handoff:

```text
Mac: dbt/SQL/tests/docs → commit/push
Windows: pull → Power BI Refresh/DAX/PBIR/UAT → commit/push
Mac: pull → final static checks
```

Power BI Desktop is installed and used only in the Windows VM; it is not part of
the Mac environment. The generic `<YOUR_MAC_LOCAL_HOSTNAME>.local:5433`
placeholder exists only to explain how a Windows VM can reach PostgreSQL on a
Mac; it is not a Mac runtime setting and must not be replaced with a personal
hostname in tracked files.

For a new Codex session on Mac, this file and `PROJECT_PLAYBOOK.md` are the
handoff context. Codex should inspect the current branch and working tree,
continue from `Next Step`, and treat `Current Blockers and Unapproved Decisions`
as scope boundaries.

Close Power BI before every pull on Windows. Do not transport `.env`, database
credentials, `.pbi` cache, generated CSV, database dumps or the personal Mac
hostname through Git.

## Project Objective

The project demonstrates an end-to-end analytics-engineering workflow for a synthetic B2B SaaS product: deterministic source generation, contract validation, PostgreSQL ingestion, dbt transformations, data-quality controls, and BI-oriented marts.

## Deterministic Baseline

- Workspaces: 200 total, 187 active
- Users: 2,500 total, 2,235 active, 265 soft-deleted
- Sessions: 1,297 with exactly one earliest first session per participating user
- Subscriptions: 180, including 111 active, 18 trial, 15 past due, and 36 cancelled
- Plan-history periods: 234, including 25 upgrades and 29 downgrades
- Invoices: 935, including 867 paid, 28 failed, and 40 pending
- Product events: 5,000

## Controlled Quality Scenarios

- Invalid raw user creation timestamps: 25
- Missing user countries: 49
- Missing invoice currencies: 22
- Invoice amount reconciliation mismatches: 16
- Duplicate workspace, user, subscription, plan-period, and invoice IDs: 0
- Sessions before a valid user creation timestamp: 0
- Overlapping plan-history periods: 0
- Free-plan invoices: 0

## Analytics Capabilities

The current marts support:

- workspace segmentation and lifecycle analysis;
- owner-based first-touch acquisition;
- active, trial, past-due, cancelled, and reactivated subscriptions;
- upgrade and downgrade history without changing subscription identity;
- billed and paid invoice analysis using separate issue, due, service, and payment dates;
- explicit invoice eligibility and Data Quality reporting;
- source-currency monthly billing and provisional USD conversion;
- product engagement by workspace, event, and session.

## Remaining Work

- Approve currency fallback and authoritative FX-date rules.
- Add recognized revenue, MRR, ARR, aging, and retention marts.
- Complete the current core-metric certification before expanding the dashboard.
- Complete the remaining Power BI pages and production Data Quality remediation
  workflow; the semantic model, initial Executive Overview, QA Revenue Trace and
  initial Data Quality Monitor are already source-controlled.
- Replace destructive raw loads with durable batch ingestion.
- Add CI/CD, orchestration, observability, secrets management, and environment separation.
