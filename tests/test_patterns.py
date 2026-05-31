import pandas as pd
from aml.synthetic import generate_transactions
from aml.patterns import (
    detect_structuring_pattern,
    detect_smurfing_pattern,
    detect_round_tripping,
    detect_cash_intensive,
    run_all,
)


def test_structuring_returns_dataframe():
    df = generate_transactions(n=500)
    result = detect_structuring_pattern(df)
    assert isinstance(result, pd.DataFrame)


def test_structuring_required_columns():
    df = generate_transactions(n=500)
    result = detect_structuring_pattern(df)
    required = [
        "sender_id", "typology", "transaction_count",
        "total_amount", "risk_score", "fincen_reference"
    ]
    for col in required:
        assert col in result.columns


def test_structuring_typology_label():
    df = generate_transactions(n=500)
    result = detect_structuring_pattern(df)
    if len(result) > 0:
        assert (result["typology"] == "structuring").all()


def test_smurfing_returns_dataframe():
    df = generate_transactions(n=500)
    result = detect_smurfing_pattern(df)
    assert isinstance(result, pd.DataFrame)


def test_smurfing_required_columns():
    df = generate_transactions(n=500)
    result = detect_smurfing_pattern(df)
    required = [
        "receiver_id", "typology", "unique_senders",
        "transaction_count", "total_amount", "risk_score"
    ]
    for col in required:
        assert col in result.columns


def test_round_tripping_returns_dataframe():
    df = generate_transactions(n=500)
    result = detect_round_tripping(df)
    assert isinstance(result, pd.DataFrame)


def test_cash_intensive_returns_dataframe():
    df = generate_transactions(n=500)
    result = detect_cash_intensive(df)
    assert isinstance(result, pd.DataFrame)


def test_cash_intensive_ratio_below_one():
    df = generate_transactions(n=500)
    result = detect_cash_intensive(df)
    if len(result) > 0:
        assert (result["cash_ratio"] <= 1.0).all()


def test_risk_scores_between_zero_and_one():
    df = generate_transactions(n=500)
    result = detect_structuring_pattern(df)
    if len(result) > 0:
        assert (result["risk_score"] >= 0).all()
        assert (result["risk_score"] <= 1).all()


def test_run_all_returns_dict():
    df = generate_transactions(n=500)
    results = run_all(df)
    assert isinstance(results, dict)


def test_run_all_has_all_typologies():
    df = generate_transactions(n=500)
    results = run_all(df)
    for key in ["structuring", "smurfing", "round_tripping", "cash_intensive", "summary"]:
        assert key in results


def test_run_all_subset():
    df = generate_transactions(n=500)
    results = run_all(df, typologies=["structuring", "smurfing"])
    assert "structuring" in results
    assert "smurfing" in results
    assert "round_tripping" not in results