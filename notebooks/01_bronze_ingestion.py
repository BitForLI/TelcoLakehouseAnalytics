# Databricks notebook source
# ruff: noqa: F821
"""Incrementally ingest immutable customer snapshots into the Bronze Delta table."""

from delta.tables import DeltaTable
from pyspark.sql import functions as F
from pyspark.sql import types as T

catalog = dbutils.widgets.get("catalog")
schema_name = dbutils.widgets.get("schema")
source_path = dbutils.widgets.get("source_path")
snapshot_date = dbutils.widgets.get("snapshot_date")

spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{schema_name}`")
bronze_table = f"{catalog}.{schema_name}.bronze_customer_churn"

source_schema = T.StructType(
    [
        T.StructField("customerID", T.StringType(), True),
        T.StructField("gender", T.StringType(), True),
        T.StructField("SeniorCitizen", T.StringType(), True),
        T.StructField("Partner", T.StringType(), True),
        T.StructField("Dependents", T.StringType(), True),
        T.StructField("tenure", T.StringType(), True),
        T.StructField("PhoneService", T.StringType(), True),
        T.StructField("MultipleLines", T.StringType(), True),
        T.StructField("InternetService", T.StringType(), True),
        T.StructField("OnlineSecurity", T.StringType(), True),
        T.StructField("OnlineBackup", T.StringType(), True),
        T.StructField("DeviceProtection", T.StringType(), True),
        T.StructField("TechSupport", T.StringType(), True),
        T.StructField("StreamingTV", T.StringType(), True),
        T.StructField("StreamingMovies", T.StringType(), True),
        T.StructField("Contract", T.StringType(), True),
        T.StructField("PaperlessBilling", T.StringType(), True),
        T.StructField("PaymentMethod", T.StringType(), True),
        T.StructField("MonthlyCharges", T.StringType(), True),
        T.StructField("TotalCharges", T.StringType(), True),
        T.StructField("Churn", T.StringType(), True),
    ]
)

raw = (
    spark.read.option("header", True)
    .option("mode", "PERMISSIVE")
    .schema(source_schema)
    .csv(source_path)
)

business_columns = [column.name for column in source_schema]
bronze = (
    raw.withColumn("snapshot_date", F.to_date(F.lit(snapshot_date)))
    .withColumn("_ingested_at", F.current_timestamp())
    .withColumn("_source_file", F.input_file_name())
    .withColumn(
        "_record_hash",
        F.sha2(
            F.concat_ws(
                "||",
                F.col("snapshot_date").cast("string"),
                *[F.coalesce(F.col(column), F.lit("")) for column in business_columns],
            ),
            256,
        ),
    )
)

if spark.catalog.tableExists(bronze_table):
    (
        DeltaTable.forName(spark, bronze_table)
        .alias("target")
        .merge(bronze.alias("source"), "target._record_hash = source._record_hash")
        .whenNotMatchedInsertAll()
        .execute()
    )
else:
    bronze.write.format("delta").mode("overwrite").saveAsTable(bronze_table)

dbutils.jobs.taskValues.set(key="bronze_row_count", value=bronze.count())
