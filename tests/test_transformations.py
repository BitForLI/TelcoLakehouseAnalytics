from decimal import Decimal

from telco_analytics.transformations import transform_customer


def test_transform_customer_adds_reusable_business_features(customer_row):
    record = transform_customer(customer_row(), "2026-09-02")

    assert record.tenure_band == "00-12 months"
    assert record.payment_group == "Manual"
    assert record.support_status == "No tech support"
    assert record.service_count == 4
    assert record.monthly_charges == Decimal("89.50")
    assert record.churned is True


def test_blank_total_charges_is_zero_for_new_customer(customer_row):
    record = transform_customer(
        customer_row(tenure="0", TotalCharges="", Churn="No"),
        "2026-09-02",
    )

    assert record.total_charges == Decimal("0")
