# Summary — SaaS Analytics Case

## 🎯 Project Objective
This repository showcases a practical analytics engineering workflow for a B2B subscription-based SaaS product. The project covers synthetic data generation, ingestion into PostgreSQL, transformation with dbt, and a structure suitable for downstream BI reporting for business customers.

## 🧱 What This Project Demonstrates
- An end-to-end data pipeline from raw data to analytics-ready models
- A medallion-style structure: raw → staging → marts
- A local PostgreSQL environment with reproducible setup
- Python-based data generation and loading scripts
- dbt models and data-quality checks for a realistic B2B analytics workflow

## 📊 Core Metrics
These figures are illustrative example metrics used to frame the business story of the case. They are not produced automatically by the current repository pipeline from the generated synthetic dataset.

The generator and CSVs currently support the following verified facts:
- **Users generated:** 2,500
- **Sessions generated:** 1,000
- **Subscriptions generated:** 200
- **Invoices generated:** 2,280
- **Events generated:** 5,000
- **Invalid signup dates:** 240
- **Deleted users:** 114
- **Subscriptions with missing status:** 60
- **Negative invoice amounts:** 241
- **Unpaid invoices:** 118
- **Duplicate subscription identifiers:** 1
- **Duplicate invoice identifiers:** 23

## 📈 Key Insights
The dataset is intentionally designed to include data-quality issues rather than a perfectly clean SaaS history. The most visible patterns from the current synthetic data are:
- A meaningful share of records contains invalid or inconsistent values, especially around signup dates and invoice amounts.
- Subscription status is missing for a noticeable subset of records.
- Invoice quality issues are present, including negative amounts and unpaid invoices.
- The data model is suitable for demonstrating staging, quality checks, and analytics-layer design rather than for claiming business performance outcomes.

## 📊 What Can Be Analyzed in Power BI
Once the data is loaded into the analytics layer, Power BI can be used to answer practical business questions such as:
- How many users, subscriptions, invoices, and events are present in the data model?
- Which records are affected by data-quality issues such as invalid dates, missing statuses, or negative amounts?
- How do subscription and invoice quality problems impact downstream reporting?
- Which dimensions can be used for segmentation, such as plan type, workspace, payment status, or acquisition channel?
- How would a dashboard surface data quality issues before business stakeholders rely on the metrics?

Example KPI and dashboard scenarios:
- **Customer volume:** total users and active subscriptions by month
- **Billing health:** paid vs unpaid invoices, negative amounts, and missing subscription statuses
- **Multi-currency reporting:** bringing invoices from different currencies into a common reporting view and highlighting the need for conversion logic
- **Product engagement:** event counts by event type and date
- **Data-quality monitoring:** a dashboard that highlights invalid records and anomaly rates
- **Business readiness:** a report showing how much of the metric story is trustworthy once quality checks are applied

The repository includes a demonstrative implementation of this pattern: a sample FX rates dataset is loaded from [data/fx_rates.csv](data/fx_rates.csv), exposed through dbt as a staging model, and joined to invoices in a converted invoice mart model. In a production environment, this would be extended into a scheduled ingestion flow that refreshes rates from a finance source and adds stronger handling for missing or late rates.

These questions are important because they show not only how to calculate metrics, but also how to make the reporting layer robust, trustworthy, and production-ready.

## ✅ Current Status
The repository currently includes a working local pipeline for:
- PostgreSQL initialization and schema setup
- Synthetic data generation
- Raw-data loading into PostgreSQL
- dbt staging models, marts, and data-quality tests
- historical FX-rate loading and invoice conversion to USD

## 🔜 Next Steps
The next logical step is to extend the project with more mature analytics engineering capabilities, including:
- incremental data loading
- richer business metrics and documented KPI definitions
- stronger data-quality and observability practices
- BI artifacts such as dashboards and semantic models

## 🧑‍💻 Author
**Aleksei** — Python backend and data analyst.
Skills: SQL, Python, dbt, PostgreSQL, and analytics engineering.
