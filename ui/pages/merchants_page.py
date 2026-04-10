from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSplitter, QFrame
)

from core import analyzer
from core.store import AppStore
from ui.safe_slot import safe_slot
from ui.theme import ACCENT, CHART_COLORS
from ui.widgets.chart_canvas import ChartCanvas
from ui.widgets.sortable_table import SortableTable


class MerchantsPage(QWidget):
    def __init__(self, store: AppStore, parent=None) -> None:
        super().__init__(parent)
        self._store = store
        self._merchant_data: list[dict] = []
        self._build_ui()
        store.data_changed.connect(self.refresh)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title = QLabel("Merchants")
        title.setObjectName("page_title")
        layout.addWidget(title)

        hint = QLabel("Click a merchant to see their monthly spend breakdown.")
        hint.setStyleSheet("color: #666666; font-size: 12px;")
        layout.addWidget(hint)

        splitter = QSplitter(Qt.Orientation.Vertical)

        # Table
        self._table = SortableTable(
            ["Merchant", "Sub-Category", "Total Spend", "# Transactions", "Avg Transaction", "Last Seen"]
        )
        self._table.row_clicked.connect(self._on_merchant_clicked)
        splitter.addWidget(self._table)

        # Detail panel
        detail = QWidget()
        detail_layout = QVBoxLayout(detail)
        detail_layout.setContentsMargins(0, 8, 0, 0)
        detail_layout.setSpacing(8)
        self._detail_label = QLabel("Select a merchant above")
        self._detail_label.setObjectName("section_title")
        detail_layout.addWidget(self._detail_label)
        self._detail_chart = ChartCanvas(figsize=(10, 2.5))
        detail_layout.addWidget(self._detail_chart)
        splitter.addWidget(detail)

        splitter.setSizes([350, 220])
        layout.addWidget(splitter)

    @safe_slot
    def refresh(self) -> None:
        df = self._store.df
        if df is None or df.empty:
            return

        summary = analyzer.merchant_summary(df)
        self._merchant_data = summary.to_dict("records")

        rows = []
        for r in self._merchant_data:
            rows.append([
                r["clean_merchant"],
                r.get("sub_category", "") or "—",
                f"${r['total_spend']:,.2f}",
                str(r["transaction_count"]),
                f"${r['avg_transaction']:,.2f}",
                str(r["last_seen"]),
            ])
        self._table.populate(rows, [
            Qt.AlignmentFlag.AlignVCenter,
            Qt.AlignmentFlag.AlignVCenter,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
            Qt.AlignmentFlag.AlignVCenter,
        ])

    def _on_merchant_clicked(self, row: int) -> None:
        merchant = self._table.item(row, 0)
        if merchant is None:
            return
        merchant_name = merchant.text()
        df = self._store.df
        if df is None:
            return

        monthly = analyzer.merchant_monthly(df, merchant_name)
        total = monthly["total_spend"].sum()
        self._detail_label.setText(f"{merchant_name}  —  ${total:,.0f} total")

        def draw(fig):
            ax = fig.add_subplot(111)
            if monthly.empty:
                ax.text(0.5, 0.5, "No data", ha="center", va="center",
                        transform=ax.transAxes, color="#979797")
                ax.axis("off")
                return
            ax.bar(monthly["month_label"], monthly["total_spend"],
                   color=ACCENT, alpha=0.85, width=0.6)
            ax.set_facecolor("#FFFFFF")
            fig.patch.set_facecolor("#FFFFFF")
            ax.set_xlabel("Month", fontsize=10, color="#666666", labelpad=6)
            ax.set_ylabel("Net Spend ($)", fontsize=10, color="#666666", labelpad=6)
            ax.tick_params(axis="x", rotation=45, labelsize=9)
            ax.tick_params(axis="y", labelsize=9)
            ax.yaxis.set_major_formatter(lambda x, _: f"${x:,.0f}")
            ax.grid(axis="y", color="#EEEEEE", linewidth=0.8)
            ax.spines[["top", "right", "left"]].set_visible(False)
            ax.spines["bottom"].set_color("#979797")

        self._detail_chart.update_figure(draw)
