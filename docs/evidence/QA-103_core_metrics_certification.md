# QA-103 Core Metrics Certification Evidence

## Status

- Date: `2026-08-04`
- Branch: `fix/pbi-core-metrics`
- Starting commit: `d17222a4`
- Result: `MAC COMPLETE — WINDOWS DAX / VISUAL UAT PENDING`

This checkpoint certifies the local PostgreSQL, dbt, SQL reconciliation and
static PBIP baseline. It does not claim that live DAX or report visuals have
been certified; those checks require Power BI Desktop in the Windows VM.

## Scope

In scope:

- refresh the deterministic local raw batch with the existing FX file;
- run the complete dbt and independent SQL validation baseline;
- capture no-filter and control-slice SQL values;
- trace one eligible invoice and one amount-mismatch invoice to source rows;
- correct the approved `canceled` → `cancelled` DAX predicate;
- run static PBIP validation.

Out of scope:

- billed amount, open receivable, cash collected or recognized revenue;
- historical `Active Paid Workspaces` as-of logic;
- currency fallback or authoritative FX-date changes;
- DQ visual filter and interaction UAT;
- any Power BI Desktop changes on Mac.

## Mac Baseline

Command:

```bash
./scripts/run_local_pipeline.sh --skip-fx
```

Result:

```text
dbt build: Completed successfully
PASS=427 WARN=0 ERROR=0 SKIP=0 TOTAL=427
SQL audit: FINAL RESULT: PASS - all automated SQL checks passed.
PBIP validator: Power BI project structure is valid.
```

The refreshed raw batch used load batch
`f9cf391f-34fa-41cf-b117-2aa148db0e5e` at
`2026-08-04 17:16:25.574562+00`. The pipeline produced no tracked Git diff.

## PostgreSQL Reconciliation

### No report filters

| Metric | SQL value |
| --- | ---: |
| Invoices | 935 |
| Eligible Invoices | 835 |
| Net Revenue USD | 136280.411590 |
| Tax Revenue USD | 27256.082314 |
| Gross Revenue USD | 163536.493904 |
| Subscriptions | 180 |
| Active Subscriptions | 111 |
| Cancelled Subscriptions | 36 |
| Paid Workspaces — current DAX meaning | 170 |
| Active Paid Workspaces — current DAX meaning | 111 |

`Net Revenue USD` is the current technical measure name. Its documented
business meaning remains `Eligible Paid Invoice Net USD (by issue date)`.

### Control slices

| Slice | Invoices | Eligible invoices | Net Revenue USD |
| --- | ---: | ---: | ---: |
| Invoice month `2024-03` | 75 | 69 | 14484.322947 |
| `plan_id = 2` | 469 | 420 | 20714.030158 |
| `workspace_id = WS_0001` | 13 | 10 | 2157.675350 |

These are PostgreSQL expectations for Windows DAX Query View and report UAT.

## Business-ID Trace

### Eligible invoice `10001`

Source CSV row:

```text
10001,1001,WS_0001,3,monthly,2023-04-01,2023-04-15,2023-04-01,2023-04-30,GBP,79.0,15.8,94.8,paid,2023-04-02
```

Lineage evidence:

| Layer | Key evidence |
| --- | --- |
| `data/invoices.csv` | Data row `1`, `invoice_id=10001` |
| `raw.invoices` | `source_file=invoices.csv`, `source_row_number=1`, matching batch ID |
| `staging.stg_invoices` | `difference=0.00`, missing currency `false`, mismatch `false` |
| `marts.fct_invoices` | analytics eligible `true`, analytics net amount `79.00` |
| `marts.fct_invoices_converted` | GBP FX `1.236920`, analytics net USD `97.716680` |

### Amount-mismatch invoice `10062`

Source CSV row:

```text
10062,1009,WS_0009,2,monthly,2023-06-17,2023-07-01,2023-06-17,2023-07-16,USD,29.0,5.8,39.8,paid,2023-06-20
```

Lineage evidence:

| Layer | Key evidence |
| --- | --- |
| `data/invoices.csv` | Data row `62`, `invoice_id=10062` |
| `raw.invoices` | `source_file=invoices.csv`, `source_row_number=62`, matching batch ID |
| `staging.stg_invoices` | `39.80 - 29.00 - 5.80 = 5.00`, mismatch `true` |
| `marts.fct_invoices` | analytics eligible `false`, analytics amounts `NULL` |
| `marts.fct_invoices_converted` | analytics net USD remains `NULL` |

This record must be visible in the mismatch detail after the Windows visual
filter and interaction UAT, but it must not contribute to the eligible invoice
amount KPI.

## Approved DAX Correction

The data contract and `staging.stg_subscriptions` use `cancelled`. The previous
measure filtered `canceled`, so it could not count the 36 valid cancelled
subscriptions.

The source-controlled measure now uses:

```DAX
fct_subscriptions[subscription_status] = "cancelled"
```

Expected no-filter result after Windows refresh: `36`.

## Windows Handoff

- [ ] Pull the branch with Power BI Desktop closed.
- [ ] Refresh the semantic model.
- [ ] Confirm `Canceled Subscriptions = 36` in DAX Query View and the visual.
- [ ] Compare no-filter KPI values with this evidence.
- [ ] Compare invoice month `2024-03`, `plan_id = 2` and
      `workspace_id = WS_0001` control slices.
- [ ] Add the approved invoice mismatch visual-level `TRUE` filter.
- [ ] Confirm chart-to-detail interaction filters to mismatch rows.
- [ ] Confirm `invoice_id=10062` is visible and `invoice_id=10001` is excluded
      from the mismatch detail.
- [ ] Update this file with DAX/visual results and screenshots or exact values.

Until these items pass, the branch is not a certified Power BI release.
