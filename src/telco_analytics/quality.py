"""Data-contract and row-level quality checks."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation

from .models import QualityIssue

REQUIRED_COLUMNS = {
    "customerID",
    "gender",
    "SeniorCitizen",
    "Partner",
    "Dependents",
    "tenure",
    "PhoneService",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaperlessBilling",
    "PaymentMethod",
    "MonthlyCharges",
    "TotalCharges",
    "Churn",
}

CONTRACT_VALUES = {"Month-to-month", "One year", "Two year"}
INTERNET_VALUES = {"DSL", "Fiber optic", "No"}
YES_NO_VALUES = {"Yes", "No"}


def _value(row: Mapping[str, str], column: str) -> str:
    return (row.get(column) or "").strip()


def missing_columns(columns: set[str]) -> list[str]:
    return sorted(REQUIRED_COLUMNS - columns)


def _parse_decimal(value: str) -> Decimal | None:
    try:
        return Decimal(value.strip())
    except (InvalidOperation, AttributeError):
        return None


def _parse_integer(value: str) -> int | None:
    try:
        return int(value.strip())
    except (TypeError, ValueError):
        return None


def validate_customer_row(
    row: Mapping[str, str], *, duplicate_customer_id: bool = False
) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    customer_id = _value(row, "customerID")

    if not customer_id:
        issues.append(QualityIssue("missing_customer_id", "customerID is required"))
    elif duplicate_customer_id:
        issues.append(
            QualityIssue(
                "duplicate_customer_id",
                f"customerID {customer_id} appears more than once",
            )
        )

    tenure = _parse_integer(_value(row, "tenure"))
    if tenure is None or tenure < 0:
        issues.append(QualityIssue("invalid_tenure", "tenure must be a non-negative integer"))

    senior = _parse_integer(_value(row, "SeniorCitizen"))
    if senior not in {0, 1}:
        issues.append(QualityIssue("invalid_senior_flag", "SeniorCitizen must be 0 or 1"))

    monthly_charges = _parse_decimal(_value(row, "MonthlyCharges"))
    if monthly_charges is None or monthly_charges < 0:
        issues.append(
            QualityIssue("invalid_monthly_charges", "MonthlyCharges must be non-negative")
        )

    total_value = _value(row, "TotalCharges")
    total_charges = _parse_decimal(total_value) if total_value else None
    blank_for_new_customer = not total_value and tenure == 0
    if not blank_for_new_customer and (total_charges is None or total_charges < 0):
        issues.append(
            QualityIssue(
                "invalid_total_charges",
                "TotalCharges must be non-negative, or blank only when tenure is zero",
            )
        )

    if _value(row, "Churn") not in YES_NO_VALUES:
        issues.append(QualityIssue("invalid_churn", "Churn must be Yes or No"))

    if _value(row, "Contract") not in CONTRACT_VALUES:
        issues.append(QualityIssue("invalid_contract", "Contract contains an unknown value"))

    if _value(row, "InternetService") not in INTERNET_VALUES:
        issues.append(
            QualityIssue("invalid_internet_service", "InternetService contains an unknown value")
        )

    for column in ("Partner", "Dependents", "PhoneService", "PaperlessBilling"):
        if _value(row, column) not in YES_NO_VALUES:
            issues.append(QualityIssue(f"invalid_{column.lower()}", f"{column} must be Yes or No"))

    return issues
