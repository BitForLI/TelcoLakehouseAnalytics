from telco_analytics.quality import validate_customer_row


def test_new_customer_may_have_blank_total_charges(customer_row):
    row = customer_row(tenure="0", TotalCharges="")

    assert validate_customer_row(row) == []


def test_invalid_values_return_specific_issue_codes(customer_row):
    row = customer_row(
        customerID="",
        tenure="-1",
        MonthlyCharges="unknown",
        Churn="Maybe",
        Contract="Weekly",
    )

    codes = {issue.code for issue in validate_customer_row(row)}

    assert {
        "missing_customer_id",
        "invalid_tenure",
        "invalid_monthly_charges",
        "invalid_churn",
        "invalid_contract",
    }.issubset(codes)


def test_duplicate_customer_id_is_quarantined(customer_row):
    issues = validate_customer_row(customer_row(), duplicate_customer_id=True)

    assert "duplicate_customer_id" in {issue.code for issue in issues}


def test_missing_csv_values_are_reported_instead_of_crashing(customer_row):
    row = customer_row()
    row["customerID"] = None
    row["InternetService"] = None

    codes = {issue.code for issue in validate_customer_row(row)}

    assert {"missing_customer_id", "invalid_internet_service"}.issubset(codes)
