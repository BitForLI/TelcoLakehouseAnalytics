from telco_analytics.ai_summary import build_grounded_prompt
from telco_analytics.insights import build_ai_evidence_payload, build_stakeholder_summary
from telco_analytics.metrics import build_overall_kpis, build_segment_metrics
from telco_analytics.transformations import transform_customer


def test_summary_is_grounded_in_aggregate_metrics(customer_row):
    records = [
        transform_customer(customer_row(), "2026-09-02"),
        transform_customer(
            customer_row(
                customerID="0002-TEST",
                Contract="Two year",
                Churn="No",
                MonthlyCharges="50.00",
                TotalCharges="600.00",
            ),
            "2026-09-02",
        ),
    ]
    kpis = build_overall_kpis(records)
    metrics = build_segment_metrics(records)

    summary = build_stakeholder_summary(kpis, metrics)
    evidence = build_ai_evidence_payload(kpis, metrics)
    prompt = build_grounded_prompt(evidence)

    assert "50.0%" in summary
    assert "0001-TEST" not in summary
    assert "Do not infer causation" in prompt
    assert "customer_id" not in prompt
