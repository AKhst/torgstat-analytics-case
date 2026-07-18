# Reports

This directory contains analytics deliverables built on top of the dbt marts layer.

The Power BI implementation lives in `power_bi/`:

- `power_bi/TorgstatAnalytics.pbip` is the version-controlled project entry point.
- `power_bi/TorgstatAnalytics.SemanticModel/` stores the model as TMDL.
- `power_bi/TorgstatAnalytics.Report/` stores the report as PBIR after the first Desktop save.
- `power_bi/README.md` documents the local and Git workflows.
- `power_bi/semantic_model.md` defines the first semantic model.
- `power_bi/report_blueprint.md` defines the first report pages.

Binary `.pbix` files are intentionally not committed. PBIP, TMDL, and PBIR metadata are reviewable text and belong in Git; local `.pbi` settings and data caches do not.
