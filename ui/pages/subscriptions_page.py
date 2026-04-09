from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame
)

from core import analyzer
from core.store import AppStore
from ui.theme import GREEN, ORANGE, TEXT_SECONDARY
from ui.widgets.metric_card import MetricCard


class SubscriptionsPage(QWidget):
    def __init__(self, store: AppStore, parent=None) -> None:
        super().__init__(parent)
        self._store = store
        self._build_ui()
        store.data_changed.connect(self.refresh)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title = QLabel("Subscriptions")
        title.setObjectName("page_title")
        layout.addWidget(title)

        subtitle = QLabel(
            "Auto-detected recurring charges based on merchant, amount, and billing interval."
        )
        subtitle.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(subtitle)

        # Summary cards
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        self._card_count = MetricCard("Subscriptions Found")
        self._card_monthly = MetricCard("Est. Monthly Cost")
        self._card_annual = MetricCard("Est. Annual Cost")
        self._card_cancelled = MetricCard("Possibly Cancelled")
        for c in [self._card_count, self._card_monthly, self._card_annual, self._card_cancelled]:
            cards_row.addWidget(c)
        cards_row.addStretch()
        layout.addLayout(cards_row)

        # Table
        cols = ["Merchant", "Amount", "Cadence", "Occurrences",
                "First Seen", "Last Seen", "Est. Annual Cost", "Confidence", "Status"]
        self._table = QTableWidget(0, len(cols))
        self._table.setHorizontalHeaderLabels(cols)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSortingEnabled(True)
        layout.addWidget(self._table)

    def refresh(self) -> None:
        df = self._store.df
        if df is None or df.empty:
            return

        subs = analyzer.detect_subscriptions(df)

        total_annual = sum(s["estimated_annual_cost"] for s in subs)
        total_monthly = total_annual / 12
        cancelled = sum(1 for s in subs if s["possibly_cancelled"])

        self._card_count.set_value(str(len(subs)))
        self._card_monthly.set_value(f"${total_monthly:,.0f}/mo")
        self._card_annual.set_value(f"${total_annual:,.0f}/yr")
        self._card_cancelled.set_value(str(cancelled))

        self._table.setSortingEnabled(False)
        self._table.setRowCount(0)

        RIGHT = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
        CENTER = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter

        for s in subs:
            row = self._table.rowCount()
            self._table.insertRow(row)

            status = "Possibly Cancelled" if s["possibly_cancelled"] else "Active"
            conf_color = GREEN if s["confidence"] == "High" else ORANGE
            status_color = ORANGE if s["possibly_cancelled"] else GREEN

            data = [
                (s["merchant"], Qt.AlignmentFlag.AlignVCenter),
                (f"${s['amount']:,.2f}", RIGHT),
                (s["cadence"], CENTER),
                (str(s["occurrences"]), CENTER),
                (str(s["first_seen"]), Qt.AlignmentFlag.AlignVCenter),
                (str(s["last_seen"]), Qt.AlignmentFlag.AlignVCenter),
                (f"${s['estimated_annual_cost']:,.0f}", RIGHT),
                (s["confidence"], CENTER),
                (status, CENTER),
            ]

            for col, (val, align) in enumerate(data):
                item = QTableWidgetItem(val)
                item.setTextAlignment(align)
                if col == 7:  # Confidence
                    item.setForeground(QColor(conf_color))
                if col == 8:  # Status
                    item.setForeground(QColor(status_color))
                self._table.setItem(row, col, item)

        self._table.setSortingEnabled(True)
        self._table.resizeColumnsToContents()
