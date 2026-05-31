import pandas as pd
import numpy as np


def detect_structuring_pattern(df, threshold=9_000, window_hours=48, min_count=2):
    """
    Detect structuring — breaking up large amounts into multiple
    transactions just below the CTR reporting threshold of $10,000
    to avoid regulatory reporting obligations.

    Parameters
    ----------
    df : pd.DataFrame
        Transaction data with columns: sender_id, amount, timestamp.
    threshold : float
        Amount below which a transaction is suspicious. Default 9,000.
    window_hours : int
        Time window to group transactions. Default 48.
    min_count : int
        Minimum transactions in window to flag. Default 2.

    Returns
    -------
    pd.DataFrame
        Flagged transactions with structuring indicators.

    References
    ----------
    FinCEN Advisory FIN-2014-A005: Guidance on Structuring
    31 U.S.C. 5324 — Prohibition on structuring transactions
    """
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    window = pd.Timedelta(hours=window_hours)
    alerts = []

    for sender, group in df.groupby("sender_id"):
        group = group[group["amount"] < threshold].sort_values("timestamp")
        group = group.reset_index(drop=True)

        if len(group) < min_count:
            continue

        for i in range(len(group)):
            mask = (
                (group["timestamp"] >= group.loc[i, "timestamp"]) &
                (group["timestamp"] <= group.loc[i, "timestamp"] + window)
            )
            window_group = group[mask]

            if len(window_group) >= min_count:
                alerts.append({
                    "sender_id":         sender,
                    "typology":          "structuring",
                    "transaction_count": len(window_group),
                    "total_amount":      round(window_group["amount"].sum(), 2),
                    "avg_amount":        round(window_group["amount"].mean(), 2),
                    "window_start":      window_group["timestamp"].min(),
                    "window_end":        window_group["timestamp"].max(),
                    "risk_score":        min(1.0, round(len(window_group) * 0.15, 2)),
                    "fincen_reference":  "FIN-2014-A005",
                })
                break

    return pd.DataFrame(alerts) if alerts else pd.DataFrame(columns=[
        "sender_id", "typology", "transaction_count", "total_amount",
        "avg_amount", "window_start", "window_end", "risk_score", "fincen_reference"
    ])


def detect_smurfing_pattern(df, threshold=9_000, window_hours=24, min_senders=3):
    """
    Detect smurfing — multiple different individuals (smurfs) each
    making deposits just below the reporting threshold into the same
    receiving account within a short time window.

    Smurfing differs from structuring in that it involves multiple
    senders coordinating deposits into one receiver, rather than one
    sender breaking up their own transactions.

    Parameters
    ----------
    df : pd.DataFrame
        Transaction data with columns: sender_id, receiver_id,
        amount, timestamp.
    threshold : float
        Amount below which a transaction is suspicious. Default 9,000.
    window_hours : int
        Time window to group transactions. Default 24.
    min_senders : int
        Minimum unique senders to the same receiver to flag. Default 3.

    Returns
    -------
    pd.DataFrame
        Flagged receiver accounts with smurfing indicators.

    References
    ----------
    FATF Glossary: Smurfing (2012)
    FinCEN Advisory FIN-2014-A005: Guidance on Structuring
    """
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    window = pd.Timedelta(hours=window_hours)
    suspicious = df[df["amount"] < threshold]
    alerts = []

    for receiver, group in suspicious.groupby("receiver_id"):
        group = group.sort_values("timestamp").reset_index(drop=True)

        for i in range(len(group)):
            mask = (
                (group["timestamp"] >= group.loc[i, "timestamp"]) &
                (group["timestamp"] <= group.loc[i, "timestamp"] + window)
            )
            window_group = group[mask]
            unique_senders = window_group["sender_id"].nunique()

            if unique_senders >= min_senders:
                alerts.append({
                    "receiver_id":       receiver,
                    "typology":          "smurfing",
                    "unique_senders":    unique_senders,
                    "transaction_count": len(window_group),
                    "total_amount":      round(window_group["amount"].sum(), 2),
                    "window_start":      window_group["timestamp"].min(),
                    "window_end":        window_group["timestamp"].max(),
                    "risk_score":        min(1.0, round(unique_senders * 0.2, 2)),
                    "fincen_reference":  "FIN-2014-A005",
                })
                break

    return pd.DataFrame(alerts) if alerts else pd.DataFrame(columns=[
        "receiver_id", "typology", "unique_senders", "transaction_count",
        "total_amount", "window_start", "window_end", "risk_score", "fincen_reference"
    ])


def detect_round_tripping(df, window_hours=72, amount_tolerance=0.05):
    """
    Detect round tripping — funds sent from Account A to Account B
    and returned to Account A (or a related account) within a short
    window, often used to create the appearance of legitimate
    business transactions.

    Parameters
    ----------
    df : pd.DataFrame
        Transaction data with columns: sender_id, receiver_id,
        amount, timestamp.
    window_hours : int
        Maximum hours between outgoing and return transaction. Default 72.
    amount_tolerance : float
        Allowable difference in amount as a fraction. Default 0.05 (5%).

    Returns
    -------
    pd.DataFrame
        Flagged account pairs showing round trip patterns.

    References
    ----------
    FATF Typologies Report: Trade-Based Money Laundering (2006)
    FinCEN Advisory FIN-2012-A001: Misuse of Shell Companies
    """
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    window = pd.Timedelta(hours=window_hours)
    alerts = []

    for _, outgoing in df.iterrows():
        sender   = outgoing["sender_id"]
        receiver = outgoing["receiver_id"]
        amount   = outgoing["amount"]
        ts       = outgoing["timestamp"]

        returns = df[
            (df["sender_id"] == receiver) &
            (df["receiver_id"] == sender) &
            (df["timestamp"] > ts) &
            (df["timestamp"] <= ts + window) &
            (abs(df["amount"] - amount) / amount <= amount_tolerance)
        ]

        if len(returns) > 0:
            alerts.append({
                "account_a":        sender,
                "account_b":        receiver,
                "typology":         "round_tripping",
                "outgoing_amount":  round(amount, 2),
                "return_amount":    round(returns.iloc[0]["amount"], 2),
                "outgoing_time":    ts,
                "return_time":      returns.iloc[0]["timestamp"],
                "hours_elapsed":    round(
                    (returns.iloc[0]["timestamp"] - ts).total_seconds() / 3600, 2
                ),
                "risk_score":       0.75,
                "fincen_reference": "FIN-2012-A001",
            })

    if not alerts:
        return pd.DataFrame(columns=[
            "account_a", "account_b", "typology", "outgoing_amount",
            "return_amount", "outgoing_time", "return_time",
            "hours_elapsed", "risk_score", "fincen_reference"
        ])

    return (
        pd.DataFrame(alerts)
        .drop_duplicates(subset=["account_a", "account_b"])
        .reset_index(drop=True)
    )


def detect_cash_intensive(df, cash_threshold=0.7, min_transactions=5):
    """
    Detect cash-intensive business risk — accounts where an unusually
    high proportion of transactions are cash-based, which can indicate
    a business being used as a front to commingle illicit cash with
    legitimate revenue.

    Parameters
    ----------
    df : pd.DataFrame
        Transaction data with columns: sender_id, amount,
        channel, timestamp.
    cash_threshold : float
        Minimum fraction of cash transactions to flag. Default 0.7.
    min_transactions : int
        Minimum total transactions to include an account. Default 5.

    Returns
    -------
    pd.DataFrame
        Flagged accounts with cash activity ratios.

    References
    ----------
    FinCEN Advisory FIN-2014-A005: Guidance on Cash-Intensive Businesses
    FATF Risk-Based Approach Guidance for the Banking Sector (2014)
    """
    df = df.copy()
    alerts = []

    for sender, group in df.groupby("sender_id"):
        if len(group) < min_transactions:
            continue

        total = len(group)
        cash_count = len(group[group["channel"] == "cash"])
        cash_ratio = cash_count / total

        if cash_ratio >= cash_threshold:
            alerts.append({
                "account_id":        sender,
                "typology":          "cash_intensive",
                "total_transactions": total,
                "cash_transactions": cash_count,
                "cash_ratio":        round(cash_ratio, 4),
                "total_cash_amount": round(
                    group[group["channel"] == "cash"]["amount"].sum(), 2
                ),
                "risk_score":        round(cash_ratio * 0.9, 4),
                "fincen_reference":  "FIN-2014-A005",
            })

    if not alerts:
        return pd.DataFrame(columns=[
            "account_id", "typology", "total_transactions", "cash_transactions",
            "cash_ratio", "total_cash_amount", "risk_score", "fincen_reference"
        ])

    return (
        pd.DataFrame(alerts)
        .sort_values("cash_ratio", ascending=False)
        .reset_index(drop=True)
    )


def run_all(df, typologies=None):
    """
    Run all pattern detection functions and return a combined
    alert summary. This is the main entry point for the patterns
    module — use this for end-to-end pipeline runs.

    Parameters
    ----------
    df : pd.DataFrame
        Transaction data.
    typologies : list of str, optional
        Which typologies to run. Options: "structuring", "smurfing",
        "round_tripping", "cash_intensive".
        Defaults to all four if None.

    Returns
    -------
    dict
        Keys are typology names, values are DataFrames of alerts.
        Also includes a "summary" DataFrame with alert counts.
    """
    if typologies is None:
        typologies = ["structuring", "smurfing", "round_tripping", "cash_intensive"]

    runners = {
        "structuring":   lambda: detect_structuring_pattern(df),
        "smurfing":      lambda: detect_smurfing_pattern(df),
        "round_tripping": lambda: detect_round_tripping(df),
        "cash_intensive": lambda: detect_cash_intensive(df),
    }

    results = {}
    summary_rows = []

    for name in typologies:
        if name in runners:
            result = runners[name]()
            results[name] = result
            summary_rows.append({
                "typology":    name,
                "alert_count": len(result),
            })

    results["summary"] = pd.DataFrame(summary_rows)
    return results