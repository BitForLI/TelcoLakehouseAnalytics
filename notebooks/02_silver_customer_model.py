# Databricks notebook source
# ruff: noqa: F821
"""Apply data contracts, quarantine bad rows, and merge the curated customer model."""

from delta.tables import DeltaTable
from pyspark.sql import Window
from pyspark.sql import functions as F

catalog = dbutils.widgets.get("catalog")
schema_name = dbutils.widgets.get("schema")
snapshot_date = dbutils.widgets.get("snapshot_date")
minimum_quality_rate = float(dbutils.widgets.get("minimum_quality_rate"))

bronze_table = f"{catalog}.{schema_name}.bronze_customer_churn"
silver_table = f"{catalog}.{schema_name}.silver_customer_snapshot"
quarantine_table = f"{catalog}.{schema_name}.silver_customer_quarantine"

source = spark.table(bronze_table).where(F.col("snapshot_date") == F.to_date(F.lit(snapshot_date)))
duplicate_window = Window.partitionBy("snapshot_date", "customerID")
checked = source.withColumn("_customer_id_count", F.count("*").over(duplicate_window))


def invalid_category(column, allowed_values):
    return ~F.coalesce(F.col(column).isin(*allowed_values), F.lit(False))


valid_total_charges = (
    (F.coalesce(F.trim(F.col("TotalCharges")), F.lit("")) == "")
    & (F.col("tenure").cast("int") == 0)
) | (
    F.col("TotalCharges").cast("decimal(14,2)").isNotNull()
    & (F.col("TotalCharges").cast("decimal(14,2)") >= 0)
)
issue_candidates = F.array(
    F.when(
        F.coalesce(F.trim(F.col("customerID")), F.lit("")) == "",
        F.lit("missing_customer_id"),
    ),
    F.when(F.col("_customer_id_count") > 1, F.lit("duplicate_customer_id")),
    F.when(
        F.col("tenure").cast("int").isNull() | (F.col("tenure").cast("int") < 0),
        F.lit("invalid_tenure"),
    ),
    F.when(invalid_category("SeniorCitizen", ("0", "1")), F.lit("invalid_senior_flag")),
    F.when(
        F.col("MonthlyCharges").cast("decimal(12,2)").isNull()
        | (F.col("MonthlyCharges").cast("decimal(12,2)") < 0),
        F.lit("invalid_monthly_charges"),
    ),
    F.when(
        ~F.coalesce(valid_total_charges, F.lit(False)),
        F.lit("invalid_total_charges"),
    ),
    F.when(invalid_category("Churn", ("Yes", "No")), F.lit("invalid_churn")),
    F.when(
        invalid_category("Contract", ("Month-to-month", "One year", "Two year")),
        F.lit("invalid_contract"),
    ),
    F.when(
        invalid_category("InternetService", ("DSL", "Fiber optic", "No")),
        F.lit("invalid_internet_service"),
    ),
    *[
        F.when(invalid_category(column, ("Yes", "No")), F.lit(f"invalid_{column.lower()}"))
        for column in ("Partner", "Dependents", "PhoneService", "PaperlessBilling")
    ],
)
checked = checked.withColumn(
    "_quality_issues", F.filter(issue_candidates, lambda item: item.isNotNull())
)
invalid = checked.where(F.size("_quality_issues") > 0)
valid = checked.where(F.size("_quality_issues") == 0)

total_count = checked.count()
valid_count = valid.count()
quality_rate = valid_count / total_count if total_count else 0.0

quarantine = invalid.select(
    F.to_date(F.lit(snapshot_date)).alias("snapshot_date"),
    F.col("customerID").alias("customer_id"),
    "_source_file",
    "_record_hash",
    "_quality_issues",
    F.current_timestamp().alias("quarantined_at"),
)
(
    quarantine.write.format("delta")
    .mode("overwrite")
    .option("replaceWhere", f"snapshot_date = '{snapshot_date}'")
    .saveAsTable(quarantine_table)
)

service_columns = [
    "PhoneService",
    "MultipleLines",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
]
service_count = sum(F.when(F.col(column) == "Yes", 1).otherwise(0) for column in service_columns)

curated = valid.select(
    F.trim("customerID").alias("customer_id"),
    "snapshot_date",
    F.trim("gender").alias("gender"),
    (F.col("SeniorCitizen") == "1").alias("senior_citizen"),
    (F.col("Partner") == "Yes").alias("partner"),
    (F.col("Dependents") == "Yes").alias("dependents"),
    F.col("tenure").cast("int").alias("tenure_months"),
    F.col("InternetService").alias("internet_service"),
    F.col("TechSupport").alias("tech_support"),
    F.col("Contract").alias("contract"),
    F.col("PaymentMethod").alias("payment_method"),
    F.col("MonthlyCharges").cast("decimal(12,2)").alias("monthly_charges"),
    F.coalesce(F.col("TotalCharges").cast("decimal(14,2)"), F.lit(0)).alias("total_charges"),
    (F.col("Churn") == "Yes").alias("churned"),
    F.when(F.col("tenure").cast("int") <= 12, "00-12 months")
    .when(F.col("tenure").cast("int") <= 24, "13-24 months")
    .when(F.col("tenure").cast("int") <= 48, "25-48 months")
    .otherwise("49+ months")
    .alias("tenure_band"),
    F.when(F.lower("PaymentMethod").contains("automatic"), "Automatic")
    .otherwise("Manual")
    .alias("payment_group"),
    F.when(F.col("InternetService") == "No", "No internet service")
    .when(F.col("TechSupport") == "Yes", "Has tech support")
    .otherwise("No tech support")
    .alias("support_status"),
    service_count.alias("service_count"),
    "_record_hash",
    F.current_timestamp().alias("updated_at"),
)

if spark.catalog.tableExists(silver_table):
    (
        DeltaTable.forName(spark, silver_table)
        .alias("target")
        .merge(
            curated.alias("source"),
            "target.customer_id = source.customer_id "
            "AND target.snapshot_date = source.snapshot_date",
        )
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )
else:
    curated.write.format("delta").mode("overwrite").saveAsTable(silver_table)

dbutils.jobs.taskValues.set(key="quality_pass_rate", value=quality_rate)
dbutils.jobs.taskValues.set(key="quarantined_row_count", value=total_count - valid_count)
if quality_rate < minimum_quality_rate:
    raise ValueError(
        f"Quality pass rate {quality_rate:.2%} is below the required {minimum_quality_rate:.2%}"
    )
