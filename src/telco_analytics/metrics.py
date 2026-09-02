"""Reusable Gold-layer retention metrics."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from decimal import ROUND_HALF_UP, Decimal

from .models import CustomerRecord, SegmentMetric

MONEY_PLACES = Decimal("0.01")

SEGMENT_DIMENSIONS = {
    "contract": lambda record: record.contract,
    "internet_service": lambda record: record.internet_service,
    "tenure_band": lambda record: record.tenure_band,
    "payment_group": lambda record: record.payment_group,
    "support_status": lambda record: record.support_status,
}


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


def build_overall_kpis(records: Iterable[CustomerRecord]) -> dict[str, str | int | float]:
    rows = list(records)
    if not rows:
        raise ValueError("At least one customer record is required")

    customer_count = len(rows)
    churned = sum(record.churned for record in rows)
    monthly_revenue = sum((record.monthly_charges for record in rows), Decimal("0"))
    revenue_at_risk = sum(
        (record.monthly_charges for record in rows if record.churned), Decimal("0")
    )

    return {
        "snapshot_date": rows[0].snapshot_date,
        "customer_count": customer_count,
        "churned_customers": churned,
        "churn_rate": round(churned / customer_count, 4),
        "monthly_revenue": f"{_money(monthly_revenue):.2f}",
        "monthly_revenue_at_risk": f"{_money(revenue_at_risk):.2f}",
        "average_monthly_charges": f"{_money(monthly_revenue / customer_count):.2f}",
        "average_tenure_months": round(
            sum(record.tenure_months for record in rows) / customer_count, 2
        ),
    }


def build_segment_metrics(records: Iterable[CustomerRecord]) -> list[SegmentMetric]:
    rows = list(records)
    grouped: dict[tuple[str, str], list[CustomerRecord]] = defaultdict(list)
    for record in rows:
        for dimension, selector in SEGMENT_DIMENSIONS.items():
            grouped[(dimension, selector(record))].append(record)

    metrics: list[SegmentMetric] = []
    for (dimension, segment), members in sorted(grouped.items()):
        count = len(members)
        churned = sum(record.churned for record in members)
        revenue = sum((record.monthly_charges for record in members), Decimal("0"))
        risk = sum((record.monthly_charges for record in members if record.churned), Decimal("0"))
        metrics.append(
            SegmentMetric(
                snapshot_date=members[0].snapshot_date,
                dimension=dimension,
                segment=segment,
                customer_count=count,
                churned_customers=churned,
                churn_rate=round(churned / count, 4),
                monthly_revenue=_money(revenue),
                monthly_revenue_at_risk=_money(risk),
                average_monthly_charges=_money(revenue / count),
                average_tenure_months=round(
                    sum(record.tenure_months for record in members) / count, 2
                ),
            )
        )
    return metrics
