# Telco Lakehouse Analytics

A Databricks-ready analytics product that turns a telecommunications customer snapshot into
quality-controlled tables, reusable retention metrics, and an evidence-based stakeholder brief.

The project focuses on a practical business question: **which customer segments should a
retention team investigate first, and how can that analysis run repeatedly with minimal manual
work?**

## What it delivers

- A Bronze/Silver/Gold lakehouse workflow implemented as four Databricks notebook tasks.
- Data-contract checks, invalid-row quarantine, and a configurable quality gate.
- Idempotent Delta `MERGE` operations so retries do not duplicate customer snapshots.
- Overall and segment-level churn, revenue, tenure, and revenue-at-risk measures.
- SQL queries for KPI cards, retention priorities, snapshot trends, and quality monitoring.
- A deterministic stakeholder report whose numbers come directly from Gold metrics.
- An optional Databricks `ai_query` summary that receives aggregated evidence only.
- A dependency-light local Python runner, automated tests, linting, and GitHub Actions CI.

## Architecture

```text
CSV in a Unity Catalog Volume
              |
              v
 Bronze Delta table  -- raw values, source path, record hash
              |
              v
 Silver customer model  ---->  Quarantine table
 typed fields and features       explicit quality issues
              |
              v
 Gold KPIs + segment metrics + retention priority view
              |
        +-----+------+
        |            |
        v            v
   AI/BI SQL    Stakeholder brief
                deterministic or optional aggregate-only AI
```

See [the architecture notes](docs/architecture.md) for design and reliability decisions and
[the data dictionary](docs/data_dictionary.md) for table definitions.

## Results on the included sample

The complete IBM sample contains 7,043 customer records. A validated local run produced:

| Measure | Result |
|---|---:|
| Quality pass rate | 100.0% |
| Overall churn rate | 26.5% |
| Monthly revenue represented | $456,116.60 |
| Monthly revenue attached to churned customers | $139,130.85 |
| Month-to-month churn rate | 42.7% |
| One- and two-year contract churn rate | 6.8% |

The generated brief identifies the month-to-month group as the largest revenue-at-risk segment
and recommends testing an early-tenure retention intervention. These are descriptive
associations from a static educational dataset, not causal findings or claims about commercial
impact. See the [sample stakeholder brief](reports/sample_stakeholder_brief.md).

## Run locally

Python 3.11 or later is required. The local workflow uses only the standard library; development
tools are installed separately.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
telco-analytics --input data/raw/telco_customer_churn.csv --output data/output
```

Generated files include the curated customer snapshot, quarantined rows, Gold metrics, KPI JSON,
stakeholder brief, and a run manifest containing row counts, the quality result, and the input
SHA-256 fingerprint.

```powershell
ruff check src tests scripts notebooks
pytest
python scripts/check_outputs.py data/output/run_manifest.json
```

## Deploy to Databricks

The deployment requires a Databricks workspace with Unity Catalog access and permission to create
tables in the chosen catalog and schema.

1. Create a Unity Catalog Volume and upload the CSV to its landing directory.
2. Authenticate the Databricks CLI for the target workspace.
3. Validate and deploy the bundle, overriding values where necessary:

```powershell
databricks bundle validate
databricks bundle deploy -t dev
databricks bundle run telco_customer_analytics -t dev
```

The job is deployed with its weekly schedule paused. Set `catalog`, `schema`, `source_path`, and
`minimum_quality_rate` in bundle variables before enabling it. Supplying `ai_endpoint` enables
the optional aggregate-only AI summary; leaving it empty keeps reporting deterministic.

## Data quality and governance

- Required columns and accepted categorical values form an explicit source contract.
- Invalid numeric values, missing or duplicate IDs, and unknown categories are quarantined.
- Downstream work stops when the accepted-row rate is below the configured threshold.
- Customer identifiers never enter the optional AI prompt.
- Numeric claims in the default report are generated from current Gold-layer results.
- The run manifest makes each local execution traceable to an exact input file.

## Repository guide

| Path | Purpose |
|---|---|
| `notebooks/` | Databricks Bronze, Silver, Gold, and reporting tasks |
| `src/telco_analytics/` | Tested local implementation and reusable business logic |
| `sql/dashboard_queries.sql` | Databricks AI/BI dashboard queries |
| `resources/` and `databricks.yml` | Declarative Automation Bundle job definition |
| `tests/` | Quality, transformation, metric, report, and end-to-end tests |
| `reports/` | Example business-facing output from a validated local run |
| `docs/` | Architecture, data dictionary, and role-capability mapping |

## Attribution and scope

This project was forked from
[`tolgahancepel/telco-customer-churn`](https://github.com/tolgahancepel/telco-customer-churn)
under the MIT License and uses the public
[`Telco-Customer-Churn.csv`](https://github.com/IBM/telco-customer-churn-on-icp4d/blob/master/data/Telco-Customer-Churn.csv)
sample. See [NOTICE.md](NOTICE.md) for details.

The lakehouse workflow, quality controls, reusable analytics package, automated reporting, tests,
CI, SQL, and documentation in this fork were added by Reese Lee. The sample is not current data
from a telecommunications provider, and a live Databricks deployment requires the operator's own
workspace and permissions.

