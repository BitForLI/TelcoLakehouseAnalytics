"""Deterministic customer transformations used by the local pipeline."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from .models import CustomerRecord

SERVICE_COLUMNS = (
    "PhoneService",
    "MultipleLines",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
)


def _is_yes(value: str) -> bool:
    return value.strip() == "Yes"


def tenure_band(tenure_months: int) -> str:
    if tenure_months <= 12:
        return "00-12 months"
    if tenure_months <= 24:
        return "13-24 months"
    if tenure_months <= 48:
        return "25-48 months"
    return "49+ months"


def payment_group(payment_method: str) -> str:
    return "Automatic" if "automatic" in payment_method.lower() else "Manual"


def support_status(internet_service: str, tech_support: str) -> str:
    if internet_service == "No":
        return "No internet service"
    return "Has tech support" if tech_support == "Yes" else "No tech support"


def transform_customer(row: Mapping[str, str], snapshot_date: str) -> CustomerRecord:
    """Convert a quality-approved raw row into the curated customer model."""

    tenure = int(row["tenure"].strip())
    total_value = row["TotalCharges"].strip()
    total_charges = Decimal(total_value) if total_value else Decimal("0")
    internet = row["InternetService"].strip()
    tech_support = row["TechSupport"].strip()

    return CustomerRecord(
        customer_id=row["customerID"].strip(),
        gender=row["gender"].strip(),
        senior_citizen=row["SeniorCitizen"].strip() == "1",
        partner=_is_yes(row["Partner"]),
        dependents=_is_yes(row["Dependents"]),
        tenure_months=tenure,
        phone_service=row["PhoneService"].strip(),
        multiple_lines=row["MultipleLines"].strip(),
        internet_service=internet,
        online_security=row["OnlineSecurity"].strip(),
        online_backup=row["OnlineBackup"].strip(),
        device_protection=row["DeviceProtection"].strip(),
        tech_support=tech_support,
        streaming_tv=row["StreamingTV"].strip(),
        streaming_movies=row["StreamingMovies"].strip(),
        contract=row["Contract"].strip(),
        paperless_billing=_is_yes(row["PaperlessBilling"]),
        payment_method=row["PaymentMethod"].strip(),
        monthly_charges=Decimal(row["MonthlyCharges"].strip()),
        total_charges=total_charges,
        churned=_is_yes(row["Churn"]),
        tenure_band=tenure_band(tenure),
        payment_group=payment_group(row["PaymentMethod"].strip()),
        support_status=support_status(internet, tech_support),
        service_count=sum(_is_yes(row[column]) for column in SERVICE_COLUMNS),
        snapshot_date=snapshot_date,
    )
