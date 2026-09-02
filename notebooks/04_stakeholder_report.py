# Databricks notebook source
# ruff: noqa: F821
"""Generate a grounded stakeholder brief from aggregate Gold metrics only."""

import json

from pyspark.sql import functions as F

catalog = dbutils.widgets.get("catalog")
schema_name = dbutils.widgets.get("schema")
snapshot_date = dbutils.widgets.get("snapshot_date")
ai_endpoint = dbutils.widgets.get("ai_endpoint").strip()

kpi_table = f"{catalog}.{schema_name}.gold_retention_kpis"
priority_view = f"{catalog}.{schema_name}.gold_retention_priority"
report_table = f"{catalog}.{schema_name}.gold_stakeholder_reports"

kpi = (
    spark.table(kpi_table).where(F.col("snapshot_date") == F.to_date(F.lit(snapshot_date))).first()
)
segments = (
    spark.table(priority_view)
    .where(F.col("snapshot_date") == F.to_date(F.lit(snapshot_date)))
    .orderBy("retention_priority")
    .limit(12)
    .collect()
)

if kpi is None:
    raise ValueError(f"No Gold KPIs found for {snapshot_date}")

evidence = {
    "snapshot_date": snapshot_date,
    "kpis": kpi.asDict(recursive=True),
    "priority_segments": [row.asDict(recursive=True) for row in segments],
}
top = segments[0] if segments else None
deterministic_summary = (
    f"The {snapshot_date} snapshot contains {kpi.customer_count:,} customers with a "
    f"{kpi.churn_rate * 100:.1f}% churn rate and ${kpi.monthly_revenue_at_risk:,.2f} "
    "in monthly revenue attached to churned customers."
)
if top is not None:
    deterministic_summary += (
        f" The first retention-priority segment is {top.dimension} = {top.segment}, "
        f"with {top.customer_count:,} customers, a {top.churn_rate * 100:.1f}% churn rate, "
        f"and ${top.monthly_revenue_at_risk:,.2f} monthly revenue at risk."
    )

summary_source = "deterministic"
summary = deterministic_summary
if ai_endpoint:
    prompt = (
        "Write at most five concise bullets for a telecommunications stakeholder. "
        "Use only the supplied aggregate evidence. Every number must appear in the evidence. "
        "Do not infer causation or expose customer-level data. Finish with one testable action. "
        "Evidence: " + json.dumps(evidence, default=str, sort_keys=True)
    )
    request = spark.createDataFrame([(prompt,)], ["prompt"])
    summary = (
        request.selectExpr(
            f"ai_query('{ai_endpoint}', prompt, "
            "modelParameters => named_struct('max_tokens', 500, 'temperature', 0.1)) AS summary"
        )
        .first()
        .summary
    )
    summary_source = f"ai_query:{ai_endpoint}"

report = spark.createDataFrame(
    [(snapshot_date, summary, summary_source, json.dumps(evidence, default=str, sort_keys=True))],
    "snapshot_date string, summary string, summary_source string, evidence_json string",
).select(
    F.to_date("snapshot_date").alias("snapshot_date"),
    "summary",
    "summary_source",
    "evidence_json",
    F.current_timestamp().alias("generated_at"),
)
(
    report.write.format("delta")
    .mode("overwrite")
    .option("replaceWhere", f"snapshot_date = '{snapshot_date}'")
    .saveAsTable(report_table)
)

dbutils.jobs.taskValues.set(key="report_source", value=summary_source)
