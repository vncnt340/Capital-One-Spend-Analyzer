from __future__ import annotations

import statistics
from datetime import date

import pandas as pd

from core.analyzer import (
    monthly_totals, category_totals, merchant_summary, detect_subscriptions,
    day_of_week_totals, DAY_NAMES,
)


def generate_insights(df: pd.DataFrame) -> list[dict]:
    """
    Generate a list of plain-language insight dicts from the transaction data.
    Each dict: { "title": str, "body": str, "severity": "good"|"warning"|"info"|"bad" }
    """
    insights = []

    if df is None or df.empty:
        return insights

    spend = df[df["amount"] > 0]
    monthly = monthly_totals(df)
    cats = category_totals(df)
    merchants = merchant_summary(df)
    subs = detect_subscriptions(df)
    n_months = len(monthly)

    if n_months == 0:
        return insights

    # ── Overall spend ─────────────────────────────────────────────────────────
    total = spend["amount"].sum()
    avg_monthly = monthly["total_spend"].mean()
    total_credits = df["credit"].sum()

    insights.append({
        "title": "Overall Spending Summary",
        "body": (
            f"You have {len(spend):,} transactions across {n_months} month(s), "
            f"totaling ${total:,.2f} in gross spend. "
            f"After ${total_credits:,.2f} in credits and refunds, your net spend is "
            f"${total - total_credits:,.2f}. "
            f"Your average monthly spend is ${avg_monthly:,.2f}."
        ),
        "severity": "info",
    })

    # ── Month-over-month trend ────────────────────────────────────────────────
    if n_months >= 2:
        sorted_months = monthly.sort_values("month_label")
        recent = sorted_months.iloc[-1]
        prev = sorted_months.iloc[-2]
        change = recent["total_spend"] - prev["total_spend"]
        pct = (change / prev["total_spend"] * 100) if prev["total_spend"] > 0 else 0

        if abs(pct) >= 5:
            direction = "up" if change > 0 else "down"
            severity = "warning" if change > 0 else "good"
            insights.append({
                "title": f"Spending {direction.title()} {abs(pct):.0f}% Last Month",
                "body": (
                    f"Your spending in {recent['month_label']} was ${recent['total_spend']:,.2f}, "
                    f"{direction} ${abs(change):,.2f} ({abs(pct):.1f}%) from "
                    f"{prev['month_label']} (${prev['total_spend']:,.2f}). "
                    + ("Consider reviewing what drove the increase." if change > 0
                       else "Great job reducing your spend!")
                ),
                "severity": severity,
            })

        # Highest spend month
        peak = sorted_months.loc[sorted_months["total_spend"].idxmax()]
        if peak["month_label"] == recent["month_label"]:
            insights.append({
                "title": "This Is Your Highest Spending Month",
                "body": (
                    f"{recent['month_label']} is your highest spending month on record at "
                    f"${recent['total_spend']:,.2f}. Review recent transactions to identify "
                    f"what drove the increase."
                ),
                "severity": "bad",
            })

    # ── Top categories ────────────────────────────────────────────────────────
    if not cats.empty:
        top3 = cats.head(3)
        total_net = cats["total_spend"].sum()
        lines = []
        for _, r in top3.iterrows():
            pct = r["total_spend"] / total_net * 100
            lines.append(f"{r['category']} (${r['total_spend']:,.2f}, {pct:.0f}%)")

        insights.append({
            "title": "Your Top Spending Categories",
            "body": (
                f"Your top 3 categories make up "
                f"{top3['total_spend'].sum() / total_net * 100:.0f}% of your total spend: "
                + ", ".join(lines) + ". "
                "Focus on these first if you want to reduce overall spending."
            ),
            "severity": "info",
        })

        # Flag any category that is > 40% of total
        for _, r in cats.iterrows():
            pct = r["total_spend"] / total_net * 100
            if pct > 40:
                insights.append({
                    "title": f"{r['category']} Is Dominating Your Budget",
                    "body": (
                        f"{r['category']} accounts for {pct:.0f}% of your total spend "
                        f"(${r['total_spend']:,.2f}). This single category is consuming a "
                        f"disproportionate share of your budget — consider setting a monthly cap."
                    ),
                    "severity": "bad",
                })

    # ── Subscriptions ─────────────────────────────────────────────────────────
    if subs:
        sub_annual = sum(s["estimated_annual_cost"] for s in subs)
        sub_monthly = sub_annual / 12
        high_conf = [s for s in subs if s["confidence"] == "High"]
        cancelled = [s for s in subs if s["possibly_cancelled"]]

        insights.append({
            "title": f"You Have {len(subs)} Detected Subscription(s)",
            "body": (
                f"Your recurring charges add up to an estimated ${sub_monthly:,.2f}/month "
                f"(${sub_annual:,.2f}/year). "
                f"{len(high_conf)} are high-confidence subscriptions. "
                + (
                    f"{len(cancelled)} appear possibly cancelled (no recent charge) — "
                    f"confirm you meant to stop them."
                    if cancelled else
                    "All detected subscriptions appear to still be active."
                )
            ),
            "severity": "warning" if sub_monthly > 100 else "info",
        })

        # Flag expensive subscriptions
        expensive = [s for s in subs if s["estimated_annual_cost"] > 200]
        if expensive:
            lines = [f"{s['merchant']} (${s['estimated_annual_cost']:,.0f}/yr)" for s in expensive[:5]]
            insights.append({
                "title": "High-Cost Subscriptions to Review",
                "body": (
                    "These subscriptions cost over $200/year each — make sure you're "
                    "getting value from them: " + ", ".join(lines) + "."
                ),
                "severity": "warning",
            })

        if cancelled:
            names = ", ".join(s["merchant"] for s in cancelled[:5])
            insights.append({
                "title": "Possibly Cancelled Subscriptions",
                "body": (
                    f"These merchants haven't charged you recently and may be cancelled: "
                    f"{names}. Verify you intentionally stopped them."
                ),
                "severity": "info",
            })

    # ── Top merchants ─────────────────────────────────────────────────────────
    if not merchants.empty:
        top_m = merchants.head(1).iloc[0]
        insights.append({
            "title": f"Top Merchant: {top_m['clean_merchant']}",
            "body": (
                f"You've spent ${top_m['total_spend']:,.2f} at {top_m['clean_merchant']} "
                f"across {int(top_m['transaction_count'])} transactions "
                f"(avg ${top_m['avg_transaction']:,.2f} each). "
                "This is your single highest merchant by net spend."
            ),
            "severity": "info",
        })

        # Merchants visited very frequently
        freq = merchants[merchants["transaction_count"] >= 20].head(5)
        if not freq.empty:
            lines = [
                f"{r['clean_merchant']} ({int(r['transaction_count'])}x, ${r['avg_transaction']:,.2f} avg)"
                for _, r in freq.iterrows()
            ]
            insights.append({
                "title": "Frequent Merchants — Small Amounts Add Up",
                "body": (
                    "These merchants have 20+ transactions, meaning small purchases are "
                    "accumulating: " + ", ".join(lines) + ". "
                    "Even reducing frequency by half could meaningfully lower your spend."
                ),
                "severity": "warning",
            })

    # ── Day of week ───────────────────────────────────────────────────────────
    dow = day_of_week_totals(df)
    if not dow.empty and dow["total"].sum() > 0:
        peak_day = dow.loc[dow["total"].idxmax()]
        insights.append({
            "title": f"You Spend the Most on {DAY_NAMES[int(peak_day['day_of_week'])]}s",
            "body": (
                f"{DAY_NAMES[int(peak_day['day_of_week'])]}s account for "
                f"${peak_day['total']:,.2f} in total spend. "
                "Being mindful of spending on this day could help reduce impulse purchases."
            ),
            "severity": "info",
        })

    # ── Large one-off transactions ────────────────────────────────────────────
    threshold = avg_monthly * 0.25
    large = spend[spend["amount"] >= threshold].sort_values("amount", ascending=False).head(5)
    if not large.empty:
        lines = [
            f"{r['clean_merchant']} — ${r['amount']:,.2f} on {r['transaction_date']}"
            for _, r in large.iterrows()
        ]
        insights.append({
            "title": "Large One-Off Transactions",
            "body": (
                f"These transactions each exceed 25% of your average monthly spend "
                f"(${threshold:,.2f}): " + "; ".join(lines) + ". "
                "Review these to confirm they were planned expenses."
            ),
            "severity": "warning",
        })

    # ── Credit utilization / refunds ─────────────────────────────────────────
    if total_credits > 0:
        refund_pct = total_credits / total * 100 if total > 0 else 0
        insights.append({
            "title": f"${total_credits:,.2f} Returned via Credits & Refunds",
            "body": (
                f"You received ${total_credits:,.2f} back ({refund_pct:.1f}% of gross spend) "
                f"through refunds and credits. This has already been factored into all net spend figures."
            ),
            "severity": "good",
        })

    return insights
