# Summary — SaaS Analytics Case v1

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
- Build the Power BI semantic model and dashboard.
- Replace destructive raw loads with durable batch ingestion.
- Add CI/CD, orchestration, observability, secrets management, and environment separation.
