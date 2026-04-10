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


def _detect_bank(columns: list[str]) -> str:
    """Identify the bank from CSV column names."""
    cols = {c.strip().lower() for c in columns}

    if {"trans. date", "post date", "description", "amount", "category"}.issubset(cols):
        return "discover"

    if {"transaction date", "description", "category", "debit", "credit"}.issubset(cols):
        return "capital_one"

    return "unknown"


def _parse_capital_one(raw: pd.DataFrame) -> pd.DataFrame:
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

    df["card_no"] = raw.get("Card No.", pd.Series([""] * len(raw))).astype(str)
    df["description"] = raw["Description"].astype(str).str.strip()
    df["clean_merchant"] = df["description"].apply(_clean_merchant)
    df["category"] = raw["Category"].astype(str).str.strip().fillna("Uncategorized")
    df["sub_category"] = ""

    df["debit"] = pd.to_numeric(raw["Debit"], errors="coerce").fillna(0.0)
    df["credit"] = pd.to_numeric(raw["Credit"], errors="coerce").fillna(0.0)
    df["amount"] = df["debit"] - df["credit"]

    return df


def _parse_discover(raw: pd.DataFrame) -> pd.DataFrame:
    # Normalize column names — Discover sometimes uses slightly different casing
    raw.columns = [c.strip() for c in raw.columns]
    col_map = {c.lower(): c for c in raw.columns}

    def get_col(name: str) -> str:
        """Return the actual column name case-insensitively."""
        return col_map.get(name.lower(), name)

    required_lower = {"trans. date", "description", "amount", "category"}
    missing = required_lower - set(col_map.keys())
    if missing:
        raise LoaderError(
            f"Discover CSV is missing columns: {', '.join(missing)}\n"
            "Make sure this is a Discover transaction export."
        )

    df = pd.DataFrame()

    try:
        df["transaction_date"] = pd.to_datetime(raw[get_col("trans. date")]).dt.date
        post_col = get_col("post date")
        if post_col in raw.columns:
            df["posted_date"] = pd.to_datetime(raw[post_col]).dt.date
        else:
            df["posted_date"] = df["transaction_date"]
    except Exception as e:
        raise LoaderError(f"Could not parse dates: {e}") from e

    df["card_no"] = ""
    df["description"] = raw[get_col("description")].astype(str).str.strip()
    df["clean_merchant"] = df["description"].apply(_clean_merchant)
    df["category"] = raw[get_col("category")].astype(str).str.strip().fillna("Uncategorized")
    df["sub_category"] = ""

    # Discover: positive Amount = charge, negative = credit/payment
    amount_raw = pd.to_numeric(raw[get_col("amount")], errors="coerce").fillna(0.0)
    df["debit"] = amount_raw.clip(lower=0)
    df["credit"] = (-amount_raw).clip(lower=0)
    df["amount"] = df["debit"] - df["credit"]

    return df


def load_csv(path: str | Path) -> pd.DataFrame:
    """
    Parse a bank CSV export and return a normalized DataFrame.
    Supports: Capital One, Discover.

    Returns columns:
        transaction_date, posted_date, card_no, description,
        clean_merchant, category, sub_category, debit, credit,
        amount, month_label, day_of_week, day_of_month, bank
    """
    try:
        raw = pd.read_csv(path)
    except Exception as e:
        raise LoaderError(f"Could not read file: {e}") from e

    bank = _detect_bank(raw.columns.tolist())

    if bank == "capital_one":
        df = _parse_capital_one(raw)
    elif bank == "discover":
        df = _parse_discover(raw)
    else:
        raise LoaderError(
            "Unrecognized CSV format.\n"
            "Supported banks: Capital One, Discover.\n\n"
            f"Found columns: {', '.join(raw.columns.tolist())}"
        )

    df["bank"] = bank

    tx_dt = pd.to_datetime(df["transaction_date"])
    df["month_label"] = tx_dt.dt.strftime("%Y-%m")
    df["day_of_week"] = tx_dt.dt.dayofweek   # 0=Mon … 6=Sun
    df["day_of_month"] = tx_dt.dt.day

    df = df.sort_values("transaction_date", ascending=False).reset_index(drop=True)
    return df
