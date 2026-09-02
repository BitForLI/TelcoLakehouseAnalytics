from __future__ import annotations

import csv
import json

from telco_analytics.pipeline import run_pipeline


def test_pipeline_writes_curated_metrics_quarantine_and_report(tmp_path, customer_row):
    source = tmp_path / "customers.csv"
    output = tmp_path / "output"
    rows = [
        customer_row(),
        customer_row(customerID="0002-TEST", Churn="No", Contract="Two year"),
        customer_row(customerID="0003-BAD", Churn="Maybe"),
    ]
    with source.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    manifest = run_pipeline(
        source,
        output,
        snapshot_date="2026-09-02",
        minimum_quality_rate=0.60,
    )

    assert manifest["valid_rows"] == 2
    assert manifest["quarantined_rows"] == 1
    assert (output / "silver_customer_snapshot.csv").is_file()
    assert (output / "gold_segment_metrics.csv").is_file()
    assert "Automated Customer Retention Brief" in (output / "stakeholder_summary.md").read_text(
        encoding="utf-8"
    )
    kpis = json.loads((output / "gold_kpis.json").read_text(encoding="utf-8"))
    assert kpis["customer_count"] == 2
