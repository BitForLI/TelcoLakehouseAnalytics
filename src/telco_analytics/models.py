"""Domain models shared by the local and Databricks workflows."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal


@dataclass(frozen=True)
class QualityIssue:
    code: str
    message: str


@dataclass(frozen=True)
class CustomerRecord:
    customer_id: str
    gender: str
    senior_citizen: bool
    partner: bool
    dependents: bool
    tenure_months: int
    phone_service: str
    multiple_lines: str
    internet_service: str
    online_security: str
    online_backup: str
    device_protection: str
    tech_support: str
    streaming_tv: str
    streaming_movies: str
    contract: str
    paperless_billing: bool
    payment_method: str
    monthly_charges: Decimal
    total_charges: Decimal
    churned: bool
    tenure_band: str
    payment_group: str
    support_status: str
    service_count: int
    snapshot_date: str

    def to_csv_row(self) -> dict[str, str | int]:
        row = asdict(self)
        row["senior_citizen"] = int(self.senior_citizen)
        row["partner"] = int(self.partner)
        row["dependents"] = int(self.dependents)
        row["paperless_billing"] = int(self.paperless_billing)
        row["churned"] = int(self.churned)
        row["monthly_charges"] = f"{self.monthly_charges:.2f}"
        row["total_charges"] = f"{self.total_charges:.2f}"
        return row


@dataclass(frozen=True)
class SegmentMetric:
    snapshot_date: str
    dimension: str
    segment: str
    customer_count: int
    churned_customers: int
    churn_rate: float
    monthly_revenue: Decimal
    monthly_revenue_at_risk: Decimal
    average_monthly_charges: Decimal
    average_tenure_months: float

    def to_dict(self) -> dict[str, str | int | float]:
        return {
            "snapshot_date": self.snapshot_date,
            "dimension": self.dimension,
            "segment": self.segment,
            "customer_count": self.customer_count,
            "churned_customers": self.churned_customers,
            "churn_rate": self.churn_rate,
            "monthly_revenue": f"{self.monthly_revenue:.2f}",
            "monthly_revenue_at_risk": f"{self.monthly_revenue_at_risk:.2f}",
            "average_monthly_charges": f"{self.average_monthly_charges:.2f}",
            "average_tenure_months": self.average_tenure_months,
        }
