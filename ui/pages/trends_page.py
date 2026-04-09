from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame

from core import analyzer
from core.store import AppStore
from ui.theme import ACCENT, CHART_COLORS, GREEN
from ui.widgets.chart_canvas import ChartCanvas


class TrendsPage(QWidget):
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

        title = QLabel("Trends")
        title.setObjectName("page_title")
        self._layout.addWidget(title)

        # Day of week
        dow_label = QLabel("Spend by Day of Week")
        dow_label.setObjectName("section_title")
        self._layout.addWidget(dow_label)
        self._dow_chart = ChartCanvas(figsize=(10, 3))
        self._layout.addWidget(self._dow_chart)

        # Day of month
        dom_label = QLabel("Spend by Day of Month")
        dom_label.setObjectName("section_title")
        self._layout.addWidget(dom_label)
        self._dom_chart = ChartCanvas(figsize=(10, 3))
        self._layout.addWidget(self._dom_chart)

        # Month over month
        mom_label = QLabel("Month-over-Month Spend")
        mom_label.setObjectName("section_title")
        self._layout.addWidget(mom_label)
        self._mom_chart = ChartCanvas(figsize=(10, 3.5))
        self._layout.addWidget(self._mom_chart)

        self._layout.addStretch()
        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def refresh(self) -> None:
        df = self._store.df
        if df is None or df.empty:
            return

        # Day of week
        dow = analyzer.day_of_week_totals(df)

        def draw_dow(fig):
            ax = fig.add_subplot(111)
            bars = ax.bar(dow["day_name"], dow["total"], color=ACCENT, alpha=0.85, width=0.6)
            ax.set_facecolor("#FFFFFF")
            fig.patch.set_facecolor("#FFFFFF")
            ax.set_xlabel("Day of Week", fontsize=10, color="#666666", labelpad=6)
            ax.set_ylabel("Total Spend ($)", fontsize=10, color="#666666", labelpad=6)
            ax.yaxis.set_major_formatter(lambda x, _: f"${x:,.0f}")
            ax.grid(axis="y", color="#EEEEEE", linewidth=0.8)
            ax.spines[["top", "right", "left"]].set_visible(False)
            ax.spines["bottom"].set_color("#979797")
            ax.tick_params(labelsize=10)
            max_val = dow["total"].max()
            for bar, val in zip(bars, dow["total"]):
                if val == max_val and max_val > 0:
                    bar.set_color("#0088CC")

        self._dow_chart.update_figure(draw_dow)

        # Day of month
        dom = analyzer.day_of_month_totals(df)

        def draw_dom(fig):
            ax = fig.add_subplot(111)
            ax.bar(dom["day_of_month"], dom["total"], color=ACCENT, alpha=0.75, width=0.8)
            ax.set_facecolor("#FFFFFF")
            fig.patch.set_facecolor("#FFFFFF")
            ax.set_xlabel("Day of Month", fontsize=10, color="#666666", labelpad=6)
            ax.set_ylabel("Total Spend ($)", fontsize=10, color="#666666", labelpad=6)
            ax.yaxis.set_major_formatter(lambda x, _: f"${x:,.0f}")
            ax.grid(axis="y", color="#EEEEEE", linewidth=0.8)
            ax.spines[["top", "right", "left"]].set_visible(False)
            ax.spines["bottom"].set_color("#979797")
            ax.tick_params(labelsize=9)
            ax.set_xticks(range(1, 32))

        self._dom_chart.update_figure(draw_dom)

        # Month over month — top 5 categories stacked
        monthly = analyzer.monthly_totals(df)
        cat_totals = analyzer.category_totals(df)
        top_cats = cat_totals.head(5)["category"].tolist()

        import pandas as pd
        spend = df[df["amount"] > 0]
        pivot = (
            spend[spend["category"].isin(top_cats)]
            .groupby(["month_label", "category"])["amount"]
            .sum()
            .unstack(fill_value=0)
        )

        def draw_mom(fig):
            ax = fig.add_subplot(111)
            if pivot.empty:
                ax.text(0.5, 0.5, "Not enough data", ha="center", va="center",
                        transform=ax.transAxes, color="#979797")
                ax.axis("off")
                return
            bottom = None
            for i, cat in enumerate(pivot.columns):
                vals = pivot[cat]
                color = CHART_COLORS[i % len(CHART_COLORS)]
                if bottom is None:
                    ax.bar(pivot.index, vals, label=cat, color=color, alpha=0.85, width=0.6)
                    bottom = vals.copy()
                else:
                    ax.bar(pivot.index, vals, bottom=bottom, label=cat,
                           color=color, alpha=0.85, width=0.6)
                    bottom = bottom + vals
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
            ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18),
                      ncol=min(len(pivot.columns), 5), fontsize=9, framealpha=0,
                      borderaxespad=0)
            fig.subplots_adjust(bottom=0.22)

        self._mom_chart.update_figure(draw_mom)
