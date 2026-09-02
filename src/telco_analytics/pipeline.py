"""Locally runnable version of the Bronze/Silver/Gold analytics workflow."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections.abc import Iterable, Sequence
from datetime import UTC, date, datetime
from pathlib import Path

from .insights import build_stakeholder_summary
from .metrics import build_overall_kpis, build_segment_metrics
from .models import CustomerRecord
from .quality import missing_columns, validate_customer_row
from .transformations import transform_customer


def _write_csv(path: Path, rows: Sequence[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_and_curate(
    input_path: Path, snapshot_date: str
) -> tuple[list[CustomerRecord], list[dict[str, object]], int]:
    valid: list[CustomerRecord] = []
    quarantined: list[dict[str, object]] = []
    seen_customer_ids: set[str] = set()

    with input_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = missing_columns(columns)
        if missing:
            raise ValueError(f"Input is missing required columns: {', '.join(missing)}")

        for row_number, row in enumerate(reader, start=2):
            customer_id = row.get("customerID", "").strip()
            duplicate = bool(customer_id and customer_id in seen_customer_ids)
            issues = validate_customer_row(row, duplicate_customer_id=duplicate)
            if issues:
                quarantined.append(
                    {
                        "row_number": row_number,
                        "customer_id": customer_id,
                        "issue_codes": "|".join(issue.code for issue in issues),
                        "issue_messages": "|".join(issue.message for issue in issues),
                    }
                )
                continue

            seen_customer_ids.add(customer_id)
            valid.append(transform_customer(row, snapshot_date))

    return valid, quarantined, len(valid) + len(quarantined)


def _record_rows(records: Iterable[CustomerRecord]) -> list[dict[str, object]]:
    ordered = sorted(records, key=lambda row: row.customer_id)
    return [dict(record.to_csv_row()) for record in ordered]


def run_pipeline(
    input_path: str | Path,
    output_dir: str | Path,
    *,
    snapshot_date: str | None = None,
    minimum_quality_rate: float = 0.99,
) -> dict[str, object]:
    """Run a deterministic local equivalent of the Databricks workflow."""

    source = Path(input_path)
    destination = Path(output_dir)
    effective_date = snapshot_date or date.today().isoformat()
    date.fromisoformat(effective_date)
    if not 0 <= minimum_quality_rate <= 1:
        raise ValueError("minimum_quality_rate must be between 0 and 1")
    if not source.is_file():
        raise FileNotFoundError(source)

    records, quarantined, input_count = _load_and_curate(source, effective_date)
    if not records:
        raise ValueError("No quality-approved customer records were produced")

    quality_rate = len(records) / input_count if input_count else 0.0
    destination.mkdir(parents=True, exist_ok=True)

    curated_rows = _record_rows(records)
    metrics = build_segment_metrics(records)
    metric_rows = [metric.to_dict() for metric in metrics]
    kpis = build_overall_kpis(records)
    summary = build_stakeholder_summary(kpis, metrics)

    _write_csv(destination / "silver_customer_snapshot.csv", curated_rows)
    _write_csv(destination / "silver_quarantine.csv", quarantined)
    _write_csv(destination / "gold_segment_metrics.csv", metric_rows)
    (destination / "gold_kpis.json").write_text(
        json.dumps(kpis, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (destination / "stakeholder_summary.md").write_text(summary, encoding="utf-8")

    manifest: dict[str, object] = {
        "run_at_utc": datetime.now(UTC).isoformat(),
        "snapshot_date": effective_date,
        "input_file": source.name,
        "input_sha256": _sha256(source),
        "input_rows": input_count,
        "valid_rows": len(records),
        "quarantined_rows": len(quarantined),
        "quality_pass_rate": round(quality_rate, 6),
        "minimum_quality_rate": minimum_quality_rate,
        "quality_gate_passed": quality_rate >= minimum_quality_rate,
        "outputs": [
            "silver_customer_snapshot.csv",
            "silver_quarantine.csv",
            "gold_segment_metrics.csv",
            "gold_kpis.json",
            "stakeholder_summary.md",
        ],
    }
    (destination / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    if quality_rate < minimum_quality_rate:
        raise RuntimeError(
            f"Quality pass rate {quality_rate:.2%} is below the required {minimum_quality_rate:.2%}"
        )
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build curated telco customer data, Gold metrics and a stakeholder brief."
    )
    parser.add_argument(
        "--input",
        default="data/raw/telco_customer_churn.csv",
        help="Path to the source CSV",
    )
    parser.add_argument(
        "--output",
        default="data/output",
        help="Directory for generated analytics outputs",
    )
    parser.add_argument("--snapshot-date", help="ISO date for the customer snapshot")
    parser.add_argument(
        "--minimum-quality-rate",
        type=float,
        default=0.99,
        help="Fail the run when fewer rows pass validation",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    arguments = build_parser().parse_args(argv)
    manifest = run_pipeline(
        arguments.input,
        arguments.output,
        snapshot_date=arguments.snapshot_date,
        minimum_quality_rate=arguments.minimum_quality_rate,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
