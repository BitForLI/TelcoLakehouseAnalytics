# Architecture

## Data flow

```text
Customer snapshot CSV in Unity Catalog Volume
                    |
                    v
        Bronze: immutable raw records
        - ingestion timestamp
        - source file
        - deterministic record hash
                    |
                    v
        Silver: quality and customer model
        - invalid rows -> quarantine table
        - typed fields and reusable dimensions
        - customer + snapshot MERGE for reruns
                    |
                    v
        Gold: stakeholder analytics
        - overall retention KPIs
        - segment metrics
        - ranked revenue-at-risk view
                    |
          +---------+----------+
          |                    |
          v                    v
  AI/BI dashboard      Grounded stakeholder brief
                      deterministic by default;
                      optional ai_query on aggregates
```

## Why this design

### Bronze preserves evidence

The raw values, source path, ingestion time and record hash are retained. A hash-based Delta
`MERGE` makes rerunning the same input idempotent without deleting earlier snapshots.

### Silver separates quality from transformation

Rows that violate the contract are written to a quarantine table with explicit issue codes.
Approved rows are converted to typed, consistently named fields. Reusable features such as
tenure band, payment group and support status are computed once rather than independently in
each dashboard query.

### Gold speaks in business measures

The Gold layer exposes customer count, churn rate, monthly revenue, monthly revenue at risk,
average charges and average tenure. The same measures are grouped by contract, internet
service, tenure, payment type and support status. A ranked view gives stakeholders a starting
point for retention analysis without claiming that correlation is causation.

### AI is downstream of governed metrics

The default report is deterministic. If a Databricks model endpoint is configured, `ai_query`
receives only aggregated Gold evidence. No customer identifier or raw row is sent to the model,
and the prompt forbids unsupported numbers and causal claims.

## Reliability decisions

- A single job parameter set is inherited by all notebook tasks.
- Job concurrency is limited to one and retry intervals are explicit.
- Bronze and Silver use Delta `MERGE` keys so task retries are safe.
- Snapshot partitions in quarantine and Gold tables are replaced atomically on rerun.
- A minimum quality rate stops downstream tasks when source quality falls below the contract.
- The local runner produces a SHA-256 input fingerprint and a machine-readable run manifest.

## Deployment boundary

The bundle uses serverless notebook tasks by omitting cluster definitions. A deployment still
requires a Databricks workspace with Unity Catalog, permission to create tables in the target
schema, and a Volume containing the source CSV. `ai_query` is optional and requires a supported
serverless workspace and permission to query the selected model endpoint.
