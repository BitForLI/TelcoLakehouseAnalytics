from decimal import Decimal

from telco_analytics.metrics import build_overall_kpis, build_segment_metrics
from telco_analytics.transformations import transform_customer


def test_metrics_report_churn_and_revenue_at_risk(customer_row):
    churned = transform_customer(customer_row(), "2026-09-02")
    retained = transform_customer(
        customer_row(
            customerID="0002-TEST",
            Contract="Two year",
            Churn="No",
            MonthlyCharges="50.00",
            TotalCharges="600.00",
        ),
        "2026-09-02",
    )

    kpis = build_overall_kpis([churned, retained])
    metrics = build_segment_metrics([churned, retained])

    assert kpis["customer_count"] == 2
    assert kpis["churn_rate"] == 0.5
    assert kpis["monthly_revenue_at_risk"] == "89.50"
    month_to_month = next(
        metric
        for metric in metrics
        if metric.dimension == "contract" and metric.segment == "Month-to-month"
    )
    assert month_to_month.monthly_revenue_at_risk == Decimal("89.50")
