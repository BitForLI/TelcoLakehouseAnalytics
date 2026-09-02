-- Databricks AI/BI dashboard query examples.
-- Replace the catalog and schema identifiers when deploying outside the defaults.

-- KPI cards
SELECT
  snapshot_date,
  customer_count,
  churned_customers,
  ROUND(churn_rate * 100, 1) AS churn_rate_percent,
  monthly_revenue,
  monthly_revenue_at_risk,
  average_monthly_charges,
  average_tenure_months
FROM main.telco_lakehouse_analytics.gold_retention_kpis
QUALIFY ROW_NUMBER() OVER (ORDER BY snapshot_date DESC) = 1;

-- Retention priority table
SELECT
  dimension,
  segment,
  customer_count,
  ROUND(churn_rate * 100, 1) AS churn_rate_percent,
  monthly_revenue_at_risk,
  retention_priority
FROM main.telco_lakehouse_analytics.gold_retention_priority
WHERE snapshot_date = (
  SELECT MAX(snapshot_date)
  FROM main.telco_lakehouse_analytics.gold_retention_kpis
)
ORDER BY retention_priority, dimension, segment;

-- Snapshot trend, populated as new source snapshots arrive
SELECT
  snapshot_date,
  ROUND(churn_rate * 100, 1) AS churn_rate_percent,
  monthly_revenue_at_risk
FROM main.telco_lakehouse_analytics.gold_retention_kpis
ORDER BY snapshot_date;

-- Data quality monitoring
SELECT
  snapshot_date,
  EXPLODE(_quality_issues) AS quality_issue,
  COUNT(*) AS affected_rows
FROM main.telco_lakehouse_analytics.silver_customer_quarantine
GROUP BY snapshot_date, quality_issue
ORDER BY snapshot_date DESC, affected_rows DESC;
