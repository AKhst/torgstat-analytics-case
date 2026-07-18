# Power BI Report Blueprint

## Page 1: Executive Overview

Purpose: summarize billing health and customer scale.

Visuals:

- KPI cards: `Net Revenue USD`, `Gross Revenue USD`, `Paid Invoices`, `Payment Success Rate`, `Active Paid Workspaces`.
- Line chart: `Net Revenue USD` by `dim_date[year_month]`.
- Stacked column chart: `Net Revenue USD` by `dim_plans[plan_name]` and `dim_date[year_month]`.
- Bar chart: `Net Revenue USD` by `dim_workspaces[customer_segment]`.
- Matrix: country, active workspaces, paid workspaces, net revenue, payment success rate.

Default filters:

- Invoice date from `dim_date[date_day]`.
- Exclude blank `source_currency_code` only when presenting pure currency analysis.

## Page 2: Revenue And Plans

Purpose: understand which products and billing frequencies drive revenue.

Visuals:

- Line chart: `Net Revenue USD` and `Revenue YTD USD` by month.
- Waterfall or column chart: `Revenue MoM %` by month.
- Matrix: plan, billing frequency, invoices, eligible invoices, net revenue, average invoice net.
- Bar chart: `Net Revenue USD` by `source_currency_code`.
- Drill-through target: workspace detail from any plan or revenue visual.

## Page 3: Acquisition And Usage

Purpose: connect acquisition source, sessions, users, and product activity.

Visuals:

- KPI cards: `Workspaces`, `Active Workspaces`, `Users`, `Active Users`, `First Sessions`.
- Line chart: `Sessions By Session Date` by month.
- Bar chart: `First Sessions` by `fct_sessions[utm_source]`.
- Bar chart: `Net Revenue USD` by `dim_workspaces[acquisition_source]`.
- Scatter chart: active users versus events by workspace or segment.

Date note:

- Session and event visuals should use measures that activate their inactive date relationships.

## Page 4: Data Quality Monitor

Purpose: make controlled defects visible without polluting executive analysis.

Visuals:

- KPI cards: `Missing Invoice Currency Count`, `Invoice Amount Mismatch Count`, `Invalid User Created At Count`, `Missing User Country Count`, `FX Coverage Rate`.
- Table: invoice ID, workspace ID, plan, status, source currency, mismatch flag, missing currency flag.
- Table: user ID, workspace ID, role, country, invalid timestamp flag, missing country flag.
- Bar chart: data-quality issue counts by country or segment.

Default filters:

- Show only rows with at least one quality flag for detail tables.

## Page 5: Workspace Drill-Through

Purpose: inspect one customer account.

Drill-through field:

- `dim_workspaces[workspace_id]`

Visuals:

- Header fields: workspace name, segment, country, billing currency, acquisition source, active state.
- KPI cards: users, active users, subscriptions, invoices, net revenue, events.
- Timeline: invoice net revenue by month.
- Table: subscription and plan history.
- Table: invoice lifecycle and payment status.

## UX Notes

- Keep slicers consistent across pages: date, country, customer segment, plan, acquisition source.
- Use compact cards and matrices. This is an operational SaaS report, not a marketing page.
- Hide technical keys from normal pages after relationships are configured.
- Put data-quality flags in a dedicated page and detail tooltips, not on every executive visual.
