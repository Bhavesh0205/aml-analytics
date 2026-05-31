import pandas as pd
import numpy as np


def compute_velocity(df, window_hours=24, min_transactions=3):
    """
    Compute transaction velocity for each account over a rolling
    time window. High velocity — many transactions in a short period
    — is a key indicator of layering and rapid fund movement.

    Parameters
    ----------
    df : pd.DataFrame
        Transaction data with columns: sender_id, receiver_id,
        amount, timestamp.
    window_hours : int
        Rolling time window in hours. Default 24.
    min_transactions : int
        Minimum transactions within the window to flag. Default 3.

    Returns
    -------
    pd.DataFrame
        One row per flagged account with columns: account_id,
        window_hours, transaction_count, total_amount,
        avg_amount, first_txn, last_txn.

    References
    ----------
    FATF Guidance on AML/CFT Measures and Financial Inclusion (2012)
    FinCEN Advisory FIN-2019-A003: Payroll Tax Evasion and Cash Wages
    """
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Combine sender and receiver activity into one view
    sent = df[["sender_id", "amount", "timestamp"]].rename(
        columns={"sender_id": "account_id"}
    )
    received = df[["receiver_id", "amount", "timestamp"]].rename(
        columns={"receiver_id": "account_id"}
    )
    activity = pd.concat([sent, received]).sort_values("timestamp").reset_index(drop=True)

    alerts = []
    window = pd.Timedelta(hours=window_hours)

    for account, group in activity.groupby("account_id"):
        group = group.sort_values("timestamp").reset_index(drop=True)
        timestamps = group["timestamp"].tolist()
        amounts = group["amount"].tolist()

        for i in range(len(timestamps)):
            window_txns = []
            window_amounts = []
            for j in range(i, len(timestamps)):
                if timestamps[j] - timestamps[i] <= window:
                    window_txns.append(timestamps[j])
                    window_amounts.append(amounts[j])
                else:
                    break

            if len(window_txns) >= min_transactions:
                alerts.append({
                    "account_id":        account,
                    "window_hours":      window_hours,
                    "transaction_count": len(window_txns),
                    "total_amount":      round(sum(window_amounts), 2),
                    "avg_amount":        round(np.mean(window_amounts), 2),
                    "first_txn":         window_txns[0],
                    "last_txn":          window_txns[-1],
                })

    if not alerts:
        return pd.DataFrame(columns=[
            "account_id", "window_hours", "transaction_count",
            "total_amount", "avg_amount", "first_txn", "last_txn"
        ])

    result = (
        pd.DataFrame(alerts)
        .sort_values("transaction_count", ascending=False)
        .drop_duplicates(subset=["account_id"], keep="first")
        .reset_index(drop=True)
    )
    return result


def detect_burst_activity(df, window_hours=6, min_transactions=5):
    """
    Detect burst activity — accounts with an unusually high number
    of transactions in a very short window. More aggressive than
    compute_velocity, designed to catch rapid layering events.

    Parameters
    ----------
    df : pd.DataFrame
        Transaction data with columns: sender_id, amount, timestamp.
    window_hours : int
        Short window for burst detection. Default 6.
    min_transactions : int
        Minimum transactions to flag as a burst. Default 5.

    Returns
    -------
    pd.DataFrame
        Flagged accounts with burst activity details.
    """
    return compute_velocity(
        df,
        window_hours=window_hours,
        min_transactions=min_transactions
    )


def compute_dormancy_reactivation(df, dormant_days=90, burst_window_hours=48):
    """
    Detect dormant account reactivation — accounts that were inactive
    for a long period and then suddenly show high transaction activity.
    This pattern is common in sleeper account money laundering schemes.

    Parameters
    ----------
    df : pd.DataFrame
        Transaction data with columns: sender_id, amount, timestamp.
    dormant_days : int
        Number of days of inactivity to classify as dormant. Default 90.
    burst_window_hours : int
        Hours after reactivation to check for burst activity. Default 48.

    Returns
    -------
    pd.DataFrame
        Accounts showing dormancy followed by burst activity, with
        columns: account_id, last_activity_before_gap, reactivation_date,
        gap_days, post_reactivation_txn_count, post_reactivation_amount.

    References
    ----------
    FinCEN Advisory FIN-2016-A005: Guidance on Correspondent Banking
    """
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    sent = df[["sender_id", "amount", "timestamp"]].rename(
        columns={"sender_id": "account_id"}
    )
    activity = sent.sort_values("timestamp").reset_index(drop=True)

    alerts = []

    for account, group in activity.groupby("account_id"):
        group = group.sort_values("timestamp").reset_index(drop=True)

        if len(group) < 2:
            continue

        for i in range(1, len(group)):
            gap = group.loc[i, "timestamp"] - group.loc[i - 1, "timestamp"]
            gap_days = gap.total_seconds() / 86400

            if gap_days >= dormant_days:
                reactivation = group.loc[i, "timestamp"]
                burst_end = reactivation + pd.Timedelta(hours=burst_window_hours)
                post = group[group["timestamp"].between(reactivation, burst_end)]

                alerts.append({
                    "account_id":                   account,
                    "last_activity_before_gap":     group.loc[i - 1, "timestamp"],
                    "reactivation_date":            reactivation,
                    "gap_days":                     round(gap_days, 1),
                    "post_reactivation_txn_count":  len(post),
                    "post_reactivation_amount":     round(post["amount"].sum(), 2),
                })

    if not alerts:
        return pd.DataFrame(columns=[
            "account_id", "last_activity_before_gap", "reactivation_date",
            "gap_days", "post_reactivation_txn_count", "post_reactivation_amount"
        ])

    return (
        pd.DataFrame(alerts)
        .sort_values("gap_days", ascending=False)
        .reset_index(drop=True)
    )