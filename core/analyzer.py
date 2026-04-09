from __future__ import annotations

import re
import statistics
from datetime import date

import pandas as pd

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _spend_only(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to debit transactions (positive amount = money out)."""
    return df[df["amount"] > 0]


def monthly_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Return month_label + total_spend + net (spend - credits)."""
    out = (
        df.groupby("month_label")
        .agg(
            total_spend=("debit", "sum"),
            total_credit=("credit", "sum"),
            tx_count=("amount", "count"),
        )
        .reset_index()
        .sort_values("month_label")
    )
    out["net"] = out["total_spend"] - out["total_credit"]
    return out


def category_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Net spend per category (debits minus refunds). Excludes net-zero or net-credit categories."""
    net = (
        df.groupby("category")["amount"]
        .sum()
        .reset_index()
        .rename(columns={"amount": "total_spend"})
    )
    net = net[net["total_spend"] > 0]
    return net.sort_values("total_spend", ascending=False)


def sub_category_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Net spend per sub-category (debits minus refunds)."""
    tagged = df[df["sub_category"] != ""]
    net = (
        tagged.groupby(["category", "sub_category"])["amount"]
        .sum()
        .reset_index()
        .rename(columns={"amount": "total_spend"})
    )
    net = net[net["total_spend"] > 0]
    return net.sort_values("total_spend", ascending=False)


def merchant_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Net spend per merchant (debits minus refunds). Excludes merchants with net zero or net credit."""
    net = (
        df.groupby("clean_merchant")
        .agg(
            total_spend=("amount", "sum"),
            transaction_count=("amount", "count"),
            avg_transaction=("amount", "mean"),
            last_seen=("transaction_date", "max"),
            sub_category=("sub_category", lambda x: x[x != ""].iloc[0] if (x != "").any() else ""),
        )
        .reset_index()
    )
    net = net[net["total_spend"] > 0]
    return net.sort_values("total_spend", ascending=False)


def merchant_monthly(df: pd.DataFrame, merchant: str) -> pd.DataFrame:
    m = df[df["clean_merchant"] == merchant]
    return (
        m.groupby("month_label")["amount"]
        .sum()
        .reset_index()
        .rename(columns={"amount": "total_spend"})
        .sort_values("month_label")
    )


def day_of_week_totals(df: pd.DataFrame) -> pd.DataFrame:
    s = _spend_only(df)
    out = (
        s.groupby("day_of_week")["amount"]
        .agg(["sum", "mean", "count"])
        .reindex(range(7), fill_value=0)
        .reset_index()
        .rename(columns={"index": "day_of_week", "sum": "total", "mean": "avg", "count": "tx_count"})
    )
    out["day_name"] = out["day_of_week"].map(lambda x: DAY_NAMES[x])
    return out


def day_of_month_totals(df: pd.DataFrame) -> pd.DataFrame:
    s = _spend_only(df)
    return (
        s.groupby("day_of_month")["amount"]
        .sum()
        .reindex(range(1, 32), fill_value=0)
        .reset_index()
        .rename(columns={"amount": "total"})
    )


_SUB_SUFFIX_RE = re.compile(r"\*[A-Z0-9 ]{2,}$", re.IGNORECASE)


def _sub_merchant_key(name: str) -> str:
    """Strip unique trailing identifiers (e.g. AMAZON PRIME*AB1234 → AMAZON PRIME)."""
    return _SUB_SUFFIX_RE.sub("", name).strip()


def detect_subscriptions(df: pd.DataFrame) -> list[dict]:
    """
    Detect recurring charges using merchant + rounded amount grouping,
    interval analysis, and consistency scoring.
    """
    s = _spend_only(df)
    s = s.copy()
    s["rounded_amount"] = (s["amount"] / 0.50).round() * 0.50
    s["sub_merchant"] = s["clean_merchant"].apply(_sub_merchant_key)

    dataset_end: date = s["transaction_date"].max()
    results = []

    for (merchant, rounded_amt), group in s.groupby(["sub_merchant", "rounded_amount"]):
        dates = sorted(group["transaction_date"].tolist())
        occurrences = len(dates)
        if occurrences <= 3:
            continue

        deltas = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
        mean_delta = statistics.mean(deltas)
        cv = statistics.stdev(deltas) / mean_delta if len(deltas) > 1 else 0.0

        # Classify cadence
        if 25 <= mean_delta <= 40:
            cadence = "Monthly"
        elif 5 <= mean_delta <= 9:
            cadence = "Weekly"
        elif 340 <= mean_delta <= 390:
            cadence = "Annual"
        else:
            continue

        # Score (minimum 4 occurrences already enforced above)
        score = 0
        if occurrences >= 6:
            score += 2
        elif occurrences >= 4:
            score += 1
        if cv < 0.15:
            score += 2
        elif cv < 0.25:
            score += 1
        if cadence == "Monthly" and 28 <= mean_delta <= 31:
            score += 2
        elif cadence == "Monthly":
            score += 1
        if score < 2:
            continue

        last_seen = dates[-1]
        gap = (dataset_end - last_seen).days
        possibly_cancelled = gap > 45

        if cadence == "Monthly":
            est_annual = rounded_amt * 12
        elif cadence == "Weekly":
            est_annual = rounded_amt * 52
        else:
            est_annual = rounded_amt

        results.append({
            "merchant": merchant,
            "amount": rounded_amt,
            "cadence": cadence,
            "occurrences": occurrences,
            "first_seen": dates[0],
            "last_seen": last_seen,
            "estimated_annual_cost": est_annual,
            "confidence": "High" if score >= 4 else "Medium",
            "possibly_cancelled": possibly_cancelled,
        })

    results.sort(key=lambda x: x["estimated_annual_cost"], reverse=True)
    return results
