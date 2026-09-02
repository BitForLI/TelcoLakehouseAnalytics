from __future__ import annotations

from collections.abc import Callable

import pytest


@pytest.fixture
def customer_row() -> Callable[..., dict[str, str]]:
    def build(**overrides: str) -> dict[str, str]:
        row = {
            "customerID": "0001-TEST",
            "gender": "Female",
            "SeniorCitizen": "0",
            "Partner": "Yes",
            "Dependents": "No",
            "tenure": "8",
            "PhoneService": "Yes",
            "MultipleLines": "No",
            "InternetService": "Fiber optic",
            "OnlineSecurity": "No",
            "OnlineBackup": "Yes",
            "DeviceProtection": "No",
            "TechSupport": "No",
            "StreamingTV": "Yes",
            "StreamingMovies": "Yes",
            "Contract": "Month-to-month",
            "PaperlessBilling": "Yes",
            "PaymentMethod": "Electronic check",
            "MonthlyCharges": "89.50",
            "TotalCharges": "716.00",
            "Churn": "Yes",
        }
        row.update(overrides)
        return row

    return build
