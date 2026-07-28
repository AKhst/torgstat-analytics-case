# Portable business-case report

`artifact.json` is the canonical, source-backed report definition.
`torgstat_business_case.html` is the generated self-contained reader that can
be opened in a browser without Power BI or PostgreSQL.

Regenerate it from the repository root:

```powershell
node C:\Users\PBI_user\.codex\plugins\cache\openai-curated-remote\data-analytics\0.2.8-13ceeea1f599\skills\build-report\scripts\deliver_portable_artifact.mjs `
  --input docs\business_case_report\artifact.json `
  --output docs\business_case_report\torgstat_business_case.html
```

Generation requires Node.js; opening the committed HTML does not.

The report is a project introduction and portfolio aid. Power BI remains the
interactive analytical product; this HTML does not contain imported customer
data, database credentials, or a substitute for runtime validation.
