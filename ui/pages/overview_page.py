from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame
)

from core import analyzer
from core.store import AppStore
from ui.safe_slot import safe_slot
from ui.theme import ACCENT, CHART_COLORS
from ui.widgets.metric_card import MetricCard
from ui.widgets.chart_canvas import ChartCanvas


class OverviewPage(QWidget):
    def __init__(self, store: AppStore, parent=None) -> None:
        super().__init__(parent)
        self._store = store
        self._build_ui()
        store.data_changed.connect(self.refresh)

    def _build_ui(self) -> None:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        self._layout = QVBoxLayout(content)
        self._layout.setContentsMargins(28, 24, 28, 24)
        self._layout.setSpacing(20)

        title = QLabel("Overview")
        title.setObjectName("page_title")
        self._layout.addWidget(title)

        # Metric cards row
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        self._card_total = MetricCard("Total Spend")
        self._card_avg = MetricCard("Avg / Month")
        self._card_tx = MetricCard("Transactions")
        self._card_top_cat = MetricCard("Top Category")
        self._card_subscriptions = MetricCard("Est. Subscriptions / yr")
        for c in [self._card_total, self._card_avg, self._card_tx,
                  self._card_top_cat, self._card_subscriptions]:
            cards_row.addWidget(c)
        self._layout.addLayout(cards_row)

        # Monthly bar chart
        month_label = QLabel("Monthly Spend")
        month_label.setObjectName("section_title")
        self._layout.addWidget(month_label)
        self._monthly_chart = ChartCanvas(figsize=(10, 3))
        self._layout.addWidget(self._monthly_chart)

        # Category chart
        cat_label = QLabel("Spend by Category")
        cat_label.setObjectName("section_title")
        self._layout.addWidget(cat_label)
        self._cat_chart = ChartCanvas(figsize=(10, 4))
        self._layout.addWidget(self._cat_chart)

        self._layout.addStretch()
        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    @safe_slot
    def refresh(self) -> None:
        df = self._store.df
        if df is None or df.empty:
            return

        spend = df[df["amount"] > 0]
        total = spend["amount"].sum()
        months = df["month_label"].nunique() or 1
        avg = total / months
        tx_count = len(spend)

        cat_totals = analyzer.category_totals(df)
        top_cat = cat_totals.iloc[0]["category"] if not cat_totals.empty else "—"

        subs = analyzer.detect_subscriptions(df)
        sub_annual = sum(s["estimated_annual_cost"] for s in subs)

        self._card_total.set_value(f"${total:,.0f}")
        self._card_avg.set_value(f"${avg:,.0f}/mo")
        self._card_tx.set_value(f"{tx_count:,}")
        self._card_top_cat.set_value(top_cat)
        self._card_subscriptions.set_value(f"${sub_annual:,.0f}")

        # Monthly chart
        monthly = analyzer.monthly_totals(df)

        def draw_monthly(fig):
            ax = fig.add_subplot(111)
            ax.bar(monthly["month_label"], monthly["total_spend"],
                   color=ACCENT, alpha=0.85, width=0.6)
            ax.set_facecolor("#FFFFFF")
            fig.patch.set_facecolor("#FFFFFF")
            ax.set_xlabel("Month", fontsize=10, color="#666666", labelpad=6)
            ax.set_ylabel("Total Spend ($)", fontsize=10, color="#666666", labelpad=6)
            ax.tick_params(axis="x", rotation=45, labelsize=9)
            ax.tick_params(axis="y", labelsize=9)
            ax.yaxis.set_major_formatter(lambda x, _: f"${x:,.0f}")
            ax.grid(axis="y", color="#EEEEEE", linewidth=0.8)
            ax.spines[["top", "right", "left"]].set_visible(False)
            ax.spines["bottom"].set_color("#979797")

        self._monthly_chart.update_figure(draw_monthly)

        # Category chart
        top_cats = cat_totals.head(10)

        def draw_categories(fig):
            ax = fig.add_subplot(111)
            colors = CHART_COLORS[:len(top_cats)]
            bars = ax.barh(top_cats["category"], top_cats["total_spend"],
                           color=colors, alpha=0.85)
            ax.invert_yaxis()
            ax.set_facecolor("#FFFFFF")
            fig.patch.set_facecolor("#FFFFFF")
            ax.set_xlabel("Net Spend ($)", fontsize=10, color="#666666", labelpad=6)
            ax.set_ylabel("Category", fontsize=10, color="#666666", labelpad=6)
            ax.tick_params(axis="y", labelsize=10)
            ax.tick_params(axis="x", labelsize=9)
            ax.xaxis.set_major_formatter(lambda x, _: f"${x:,.0f}")
            ax.grid(axis="x", color="#EEEEEE", linewidth=0.8)
            ax.spines[["top", "right", "bottom"]].set_visible(False)
            ax.spines["left"].set_color("#979797")
            for bar, val in zip(bars, top_cats["total_spend"]):
                ax.text(bar.get_width() + total * 0.002, bar.get_y() + bar.get_height() / 2,
                        f"${val:,.0f}", va="center", fontsize=9, color="#666666")

        self._cat_chart.update_figure(draw_categories)
