# Power BI Semantic Model

## Model Intent

The semantic model is a star-schema reporting layer over dbt marts. Power BI should expose business-friendly fields and measures, while technical quality flags remain available for diagnostics.

Do not model directly from raw CSV extracts. The dbt layer already owns typing, quality flags, surrogate keys, and business-rule enforcement.

## Import Tables

| Table | Role | Grain |
| --- | --- | --- |
| `dim_date` | Conformed date dimension | One calendar day |
| `dim_workspaces` | Customer account dimension | One current workspace |
| `dim_users` | User dimension | One current user |
| `dim_plans` | Product plan dimension | One plan |
| `fct_subscriptions` | Subscription lifecycle fact | One subscription |
| `fct_subscription_plan_history` | Plan-change fact | One subscription plan period |
| `fct_invoices_converted` | Billing fact with USD conversion | One invoice |
| `fct_sessions` | Acquisition/session fact | One session |
| `fct_events` | Product usage event fact | One event occurrence |
| `mart_workspace_monthly_billing` | Monthly billing aggregate | One workspace, billing month, source currency |

## Relationships

Use single-direction filtering from dimensions to facts unless a specific page needs a temporary bidirectional relationship.

Sessions are filtered by workspace through the active `dim_workspaces → dim_users → fct_sessions` path. A second active direct relationship from workspace to sessions would create an ambiguous filter path, so it is intentionally omitted from TMDL.

| From | To | Cardinality | Active |
| --- | --- | --- | --- |
| `dim_workspaces[workspace_key]` | `dim_users[workspace_key]` | 1:* | Yes |
| `dim_workspaces[workspace_key]` | `fct_subscriptions[workspace_key]` | 1:* | Yes |
| `dim_workspaces[workspace_key]` | `fct_subscription_plan_history[workspace_key]` | 1:* | Yes |
| `dim_workspaces[workspace_key]` | `fct_invoices_converted[workspace_key]` | 1:* | Yes |
| `dim_workspaces[workspace_key]` | `fct_sessions[workspace_key]` | 1:* | No |
| `dim_workspaces[workspace_key]` | `fct_events[workspace_key]` | 1:* | Yes |
| `dim_workspaces[workspace_key]` | `mart_workspace_monthly_billing[workspace_key]` | 1:* | Yes |
| `dim_users[user_key]` | `fct_sessions[user_key]` | 1:* | Yes |
| `dim_plans[plan_key]` | `fct_subscription_plan_history[plan_key]` | 1:* | Yes |
| `dim_plans[plan_key]` | `fct_invoices_converted[plan_key]` | 1:* | Yes |
| `dim_date[date_day]` | `fct_invoices_converted[issued_at]` | 1:* | Yes |
| `dim_date[date_day]` | `fct_sessions[started_date]` | 1:* | No |
| `dim_date[date_day]` | `fct_events[event_date]` | 1:* | No |
| `dim_date[date_day]` | `mart_workspace_monthly_billing[billing_month]` | 1:* | No |

## Date Modeling

Mark `dim_date[date_day]` as the official Date table in Power BI.

The active date path should be invoice issue date because the first executive report is billing-led. Session, event, and monthly billing measures can activate their date paths with `USERELATIONSHIP`.

## Display Folders

Recommended measure folders:

- `Revenue`
- `Invoices`
- `Subscriptions`
- `Acquisition`
- `Product Usage`
- `Data Quality`
- `Ratios`

Recommended column folders:

- `Keys`
- `Lifecycle`
- `Billing`
- `Acquisition`
- `Quality Flags`

Hide surrogate keys from report view after relationships are created. Keep business IDs visible only on detail and drill-through pages.

## Sorting

- Sort `dim_date[month_name_short]` by `dim_date[month_number]`.
- Sort `dim_date[year_month]` by `dim_date[month_start_date]`.
- Sort `dim_plans[plan_name]` by `dim_plans[tier_rank]`.

## Assumptions

- Revenue measures use `analytics_*_amount_usd` from `fct_invoices_converted`.
- Only `is_analytics_eligible = TRUE()` invoices contribute to revenue measures.
- Failed invoices remain visible in operational invoice measures, but not in eligible revenue measures.
- MRR, ARR, recognized revenue, and currency fallback stay out of the first model until their business rules are approved.
