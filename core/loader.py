from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


class LoaderError(Exception):
    pass


# Merchant prefix patterns to strip — ordered most-specific first
_STRIP_PREFIXES = [
    r"^TST\*\s*",
    r"^SQ\s*\*\s*",
    r"^PP\*\s*",
    r"^AMZN\s*\*\s*",
    r"^VSI\*\s*",
    r"^SP\s*\s*",
    r"^APL\*\s*",
    r"^APPLE\.COM/\s*",
    r"^AUT\s*",
    r"^WHOLEFDS\s*",
    r"^\d{4,}\s*",       # leading numeric codes
]
_STRIP_RE = re.compile("|".join(_STRIP_PREFIXES), re.IGNORECASE)

# Trailing location noise: city/state abbreviations, store numbers
_TRAILING_RE = re.compile(r"\s+#\d+.*$|\s+\d{3,}.*$|\s+[A-Z]{2}\s*$", re.IGNORECASE)


def _clean_merchant(raw: str) -> str:
    name = str(raw).strip()
    name = _STRIP_RE.sub("", name)
    name = _TRAILING_RE.sub("", name)
    name = re.sub(r"\s{2,}", " ", name).strip()
    return name.title() if name else raw.strip().title()


def load_csv(path: str | Path) -> pd.DataFrame:
    """
    Parse a Capital One CSV export and return a normalized DataFrame.

    Required columns: Transaction Date, Posted Date, Card No.,
                      Description, Category, Debit, Credit

    Returns columns:
        transaction_date, posted_date, card_no, description,
        clean_merchant, category, sub_category, debit, credit,
        amount, month_label, day_of_week, day_of_month
    """
    try:
        raw = pd.read_csv(path)
    except Exception as e:
        raise LoaderError(f"Could not read file: {e}") from e

    required = {"Transaction Date", "Description", "Category", "Debit", "Credit"}
    missing = required - set(raw.columns)
    if missing:
        raise LoaderError(
            f"CSV is missing columns: {', '.join(missing)}\n"
            "Make sure this is a Capital One transaction export."
        )

    df = pd.DataFrame()

    try:
        df["transaction_date"] = pd.to_datetime(raw["Transaction Date"]).dt.date
        df["posted_date"] = pd.to_datetime(raw.get("Posted Date", raw["Transaction Date"])).dt.date
    except Exception as e:
        raise LoaderError(f"Could not parse dates: {e}") from e

    df["card_no"] = raw.get("Card No.", "").astype(str)
    df["description"] = raw["Description"].astype(str).str.strip()
    df["clean_merchant"] = df["description"].apply(_clean_merchant)
    df["category"] = raw["Category"].astype(str).str.strip().fillna("Uncategorized")
    df["sub_category"] = ""

    df["debit"] = pd.to_numeric(raw["Debit"], errors="coerce").fillna(0.0)
    df["credit"] = pd.to_numeric(raw["Credit"], errors="coerce").fillna(0.0)
    df["amount"] = df["debit"] - df["credit"]

    tx_dt = pd.to_datetime(df["transaction_date"])
    df["month_label"] = tx_dt.dt.strftime("%Y-%m")
    df["day_of_week"] = tx_dt.dt.dayofweek   # 0=Mon … 6=Sun
    df["day_of_month"] = tx_dt.dt.day

    df = df.sort_values("transaction_date", ascending=False).reset_index(drop=True)
    return df
