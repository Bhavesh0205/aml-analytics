import pandas as pd
from aml.synthetic import generate_transactions
from aml.velocity import (
    compute_velocity,
    detect_burst_activity,
    compute_dormancy_reactivation,
)


def test_compute_velocity_returns_dataframe():
    df = generate_transactions(n=500)
    result = compute_velocity(df)
    assert isinstance(result, pd.DataFrame)


def test_compute_velocity_required_columns():
    df = generate_transactions(n=500)
    result = compute_velocity(df)
    required = [
        "account_id", "window_hours", "transaction_count",
        "total_amount", "avg_amount", "first_txn", "last_txn"
    ]
    for col in required:
        assert col in result.columns, f"Missing column: {col}"


def test_compute_velocity_sorted_descending():
    df = generate_transactions(n=500)
    result = compute_velocity(df)
    if len(result) > 1:
        assert result["transaction_count"].is_monotonic_decreasing


def test_compute_velocity_amounts_positive():
    df = generate_transactions(n=500)
    result = compute_velocity(df)
    if len(result) > 0:
        assert (result["total_amount"] > 0).all()


def test_detect_burst_activity_returns_dataframe():
    df = generate_transactions(n=500)
    result = detect_burst_activity(df, window_hours=24, min_transactions=2)
    assert isinstance(result, pd.DataFrame)


def test_compute_dormancy_returns_dataframe():
    df = generate_transactions(n=500)
    result = compute_dormancy_reactivation(df, dormant_days=30)
    assert isinstance(result, pd.DataFrame)


def test_no_duplicate_accounts_in_velocity():
    df = generate_transactions(n=500)
    result = compute_velocity(df)
    assert result["account_id"].nunique() == len(result)