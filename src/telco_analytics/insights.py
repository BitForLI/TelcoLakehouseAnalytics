"""Evidence-based stakeholder summaries generated from Gold metrics."""

from __future__ import annotations

from decimal import Decimal

from .models import SegmentMetric


def _percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def _money(value: str | Decimal) -> str:
    return f"{Decimal(value):,.2f}"


def _eligible_segments(metrics: list[SegmentMetric], customer_count: int) -> list[SegmentMetric]:
    minimum_size = max(10, round(customer_count * 0.01))
    eligible = [metric for metric in metrics if metric.customer_count >= minimum_size]
    return eligible or metrics


def build_stakeholder_summary(
    kpis: dict[str, str | int | float], metrics: list[SegmentMetric]
) -> str:
    """Create a deterministic report where every claim cites a computed metric."""

    total_customers = int(kpis["customer_count"])
    eligible = _eligible_segments(metrics, total_customers)
    highest_churn = max(eligible, key=lambda metric: metric.churn_rate)
    highest_risk = max(
        eligible,
        key=lambda metric: Decimal(metric.monthly_revenue_at_risk),
    )

    contract_metrics = {
        metric.segment: metric for metric in metrics if metric.dimension == "contract"
    }
    month_to_month = contract_metrics.get("Month-to-month")
    long_contracts = [
        metric for name, metric in contract_metrics.items() if name in {"One year", "Two year"}
    ]

    lines = [
        "# Automated Customer Retention Brief",
        "",
        f"Snapshot date: **{kpis['snapshot_date']}**",
        "",
        "## Executive view",
        "",
        (
            f"- The snapshot contains **{total_customers:,} customers** with an overall "
            f"churn rate of **{_percent(float(kpis['churn_rate']))}**."
        ),
        (
            f"- Current monthly revenue is **${_money(str(kpis['monthly_revenue']))}**, of which "
            f"**${_money(str(kpis['monthly_revenue_at_risk']))}** is attached to customers marked "
            "as churned."
        ),
        (
            f"- The highest observed churn rate among sufficiently sized segments is "
            f"**{highest_churn.dimension} = {highest_churn.segment}** at "
            f"**{_percent(highest_churn.churn_rate)}** "
            f"({highest_churn.churned_customers:,}/{highest_churn.customer_count:,})."
        ),
        (
            f"- The largest monthly revenue-at-risk segment is "
            f"**{highest_risk.dimension} = {highest_risk.segment}** at "
            f"**${_money(highest_risk.monthly_revenue_at_risk)}**."
        ),
    ]

    if month_to_month and long_contracts:
        weighted_customers = sum(metric.customer_count for metric in long_contracts)
        weighted_churned = sum(metric.churned_customers for metric in long_contracts)
        long_rate = weighted_churned / weighted_customers
        lines.extend(
            [
                "",
                "## Recommended next analysis",
                "",
                (
                    f"- Month-to-month customers churn at "
                    f"**{_percent(month_to_month.churn_rate)}**, compared with "
                    f"**{_percent(long_rate)}** across one- and two-year contracts. "
                    "Validate whether an early-tenure retention offer changes this gap."
                ),
                (
                    f"- Start with the **{highest_risk.segment}** segment because it "
                    f"combines material revenue exposure "
                    f"(**${_money(highest_risk.monthly_revenue_at_risk)} per month**) with "
                    "a clearly defined customer group."
                ),
                (
                    "- Treat these findings as associations, not proof of causation; "
                    "test any intervention."
                ),
            ]
        )

    lines.extend(
        [
            "",
            "## Governance note",
            "",
            (
                "This report uses aggregated Gold-layer metrics only. "
                "It contains no customer identifiers, and every numeric statement "
                "is generated from the current pipeline output."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def build_ai_evidence_payload(
    kpis: dict[str, str | int | float], metrics: list[SegmentMetric], limit: int = 12
) -> dict[str, object]:
    """Return aggregate-only evidence suitable for an optional LLM summary."""

    ranked = sorted(
        metrics,
        key=lambda metric: Decimal(metric.monthly_revenue_at_risk),
        reverse=True,
    )[:limit]
    return {"kpis": kpis, "segments": [metric.to_dict() for metric in ranked]}
