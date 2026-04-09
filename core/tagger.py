from __future__ import annotations

import pandas as pd


def apply_rules(df: pd.DataFrame, rules: list[dict]) -> pd.DataFrame:
    """
    Apply keyword tagging rules to the description column.
    Rules are applied in order — first match wins.
    Each rule: {"keyword": str, "match_case": bool, "sub_category": str}
    """
    df = df.copy()
    df["sub_category"] = ""

    for rule in rules:
        keyword = rule.get("keyword", "")
        match_case = rule.get("match_case", False)
        sub_cat = rule.get("sub_category", "")
        if not keyword or not sub_cat:
            continue

        mask = (
            df["description"].str.contains(keyword, case=match_case, regex=False, na=False)
            & (df["sub_category"] == "")
        )
        df.loc[mask, "sub_category"] = sub_cat

    return df
