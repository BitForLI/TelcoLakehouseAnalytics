# Data Dictionary

## Bronze: `bronze_customer_churn`

All 21 source columns are retained as strings, with these operational fields added:

| Field | Type | Purpose |
|---|---|---|
| `snapshot_date` | date | Business date associated with the supplied customer snapshot |
| `_ingested_at` | timestamp | Time the record entered the lakehouse |
| `_source_file` | string | Source file used for lineage |
| `_record_hash` | string | SHA-256 value used to make repeated ingestion idempotent |

## Silver: `silver_customer_snapshot`

| Field | Type | Description |
|---|---|---|
| `customer_id` | string | Source customer identifier |
| `snapshot_date` | date | Snapshot business date |
| `tenure_months` | integer | Customer tenure in months |
| `monthly_charges` | decimal | Current monthly charge |
| `total_charges` | decimal | Cumulative charges; blank is converted to zero only for tenure zero |
| `churned` | boolean | Whether the source marks the customer as churned |
| `tenure_band` | string | 0–12, 13–24, 25–48 or 49+ months |
| `payment_group` | string | Automatic or manual payment |
| `support_status` | string | Tech support, no tech support or no internet service |
| `service_count` | integer | Count of source service flags equal to `Yes` |
| `_record_hash` | string | Link to the Bronze record |
| `updated_at` | timestamp | Time the Silver record was last merged |

## Quarantine: `silver_customer_quarantine`

The table stores the snapshot, customer ID when available, source lineage and an array of
quality issue codes. It intentionally excludes a corrected value because source-system owners
should decide how invalid business data is repaired.

## Gold: `gold_retention_kpis`

One row per snapshot with customer count, churned customers, churn rate, monthly revenue,
monthly revenue at risk, average monthly charge and average tenure.

## Gold: `gold_segment_metrics`

The same measures grouped through a tall `dimension` / `segment` model. The tall design lets a
dashboard add a new segment dimension without adding a separate physical table.

## Gold: `gold_stakeholder_reports`

Stores the deterministic or optional AI-generated summary, its source and the aggregate
evidence JSON used to create it. This makes generated text reviewable after the job completes.
