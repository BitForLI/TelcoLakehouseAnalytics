# Databricks notebook source
# ruff: noqa: F821
"""Build business-facing Gold KPIs and reusable retention segments."""

from pyspark.sql import functions as F

catalog = dbutils.widgets.get("catalog")
schema_name = dbutils.widgets.get("schema")
snapshot_date = dbutils.widgets.get("snapshot_date")

silver_table = f"{catalog}.{schema_name}.silver_customer_snapshot"
kpi_table = f"{catalog}.{schema_name}.gold_retention_kpis"
segment_table = f"{catalog}.{schema_name}.gold_segment_metrics"
priority_view = f"{catalog}.{schema_name}.gold_retention_priority"

customers = spark.table(silver_table).where(
    F.col("snapshot_date") == F.to_date(F.lit(snapshot_date))
)

kpis = customers.groupBy("snapshot_date").agg(
    F.count("*").alias("customer_count"),
    F.sum(F.col("churned").cast("int")).alias("churned_customers"),
    F.round(F.avg(F.col("churned").cast("double")), 4).alias("churn_rate"),
    F.round(F.sum("monthly_charges"), 2).alias("monthly_revenue"),
    F.round(
        F.sum(F.when(F.col("churned"), F.col("monthly_charges")).otherwise(F.lit(0))),
        2,
    ).alias("monthly_revenue_at_risk"),
    F.round(F.avg("monthly_charges"), 2).alias("average_monthly_charges"),
    F.round(F.avg("tenure_months"), 2).alias("average_tenure_months"),
)

segments = customers.selectExpr(
    "snapshot_date",
    "customer_id",
    "churned",
    "monthly_charges",
    "tenure_months",
    "stack(5, "
    "'contract', contract, "
    "'internet_service', internet_service, "
    "'tenure_band', tenure_band, "
    "'payment_group', payment_group, "
    "'support_status', support_status) AS (dimension, segment)",
)
segment_metrics = segments.groupBy("snapshot_date", "dimension", "segment").agg(
    F.count("*").alias("customer_count"),
    F.sum(F.col("churned").cast("int")).alias("churned_customers"),
    F.round(F.avg(F.col("churned").cast("double")), 4).alias("churn_rate"),
    F.round(F.sum("monthly_charges"), 2).alias("monthly_revenue"),
    F.round(
        F.sum(F.when(F.col("churned"), F.col("monthly_charges")).otherwise(F.lit(0))),
        2,
    ).alias("monthly_revenue_at_risk"),
    F.round(F.avg("monthly_charges"), 2).alias("average_monthly_charges"),
    F.round(F.avg("tenure_months"), 2).alias("average_tenure_months"),
)

for frame, table in ((kpis, kpi_table), (segment_metrics, segment_table)):
    (
        frame.write.format("delta")
        .mode("overwrite")
        .option("replaceWhere", f"snapshot_date = '{snapshot_date}'")
        .saveAsTable(table)
    )

spark.sql(
    f"""
    CREATE OR REPLACE VIEW {priority_view} AS
    SELECT
      *,
      DENSE_RANK() OVER (
        PARTITION BY snapshot_date
        ORDER BY monthly_revenue_at_risk DESC, churn_rate DESC
      ) AS retention_priority
    FROM {segment_table}
    WHERE customer_count >= 10
    """
)

dbutils.jobs.taskValues.set(key="gold_segment_count", value=segment_metrics.count())
