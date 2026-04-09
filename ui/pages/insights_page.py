from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QPushButton
)

from core.store import AppStore
from core.insights import generate_insights

_SEVERITY_STYLES = {
    "good":    {"border": "#16A34A", "bg": "#F0FDF4", "badge_bg": "#16A34A", "badge_text": "#FFFFFF", "badge": "GOOD"},
    "info":    {"border": "#4F7EF7", "bg": "#EEF2FF", "badge_bg": "#4F7EF7", "badge_text": "#FFFFFF", "badge": "INFO"},
    "warning": {"border": "#D97706", "bg": "#FFFBEB", "badge_bg": "#D97706", "badge_text": "#FFFFFF", "badge": "HEADS UP"},
    "bad":     {"border": "#DC2626", "bg": "#FEF2F2", "badge_bg": "#DC2626", "badge_text": "#FFFFFF", "badge": "ACTION NEEDED"},
}


class InsightsPage(QWidget):
    def __init__(self, store: AppStore, parent=None) -> None:
        super().__init__(parent)
        self._store = store
        self._build_ui()
        store.data_changed.connect(self.refresh)
        store.rules_changed.connect(self.refresh)

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Scrollable content
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(28, 24, 28, 24)
        self._content_layout.setSpacing(14)

        # Header row
        header_row = QHBoxLayout()
        title = QLabel("Spending Insights")
        title.setObjectName("page_title")
        header_row.addWidget(title)
        header_row.addStretch()

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.clicked.connect(self.refresh)
        header_row.addWidget(self._refresh_btn)
        self._content_layout.addLayout(header_row)

        subtitle = QLabel(
            "Rule-based analysis of your spending patterns, subscriptions, and opportunities to save. "
            "All analysis runs locally — no data leaves your machine."
        )
        subtitle.setStyleSheet("color: #666666; font-size: 12px;")
        subtitle.setWordWrap(True)
        self._content_layout.addWidget(subtitle)

        self._cards_container = QVBoxLayout()
        self._cards_container.setSpacing(12)
        self._content_layout.addLayout(self._cards_container)
        self._content_layout.addStretch()

        self._scroll.setWidget(self._content)
        outer.addWidget(self._scroll)

    def refresh(self) -> None:
        df = self._store.df

        # Clear existing cards
        while self._cards_container.count():
            item = self._cards_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if df is None or df.empty:
            placeholder = QLabel("Import a CSV to see insights.")
            placeholder.setStyleSheet("color: #979797; font-size: 13px;")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._cards_container.addWidget(placeholder)
            return

        insights = generate_insights(df)

        if not insights:
            placeholder = QLabel("Not enough data to generate insights yet.")
            placeholder.setStyleSheet("color: #979797; font-size: 13px;")
            self._cards_container.addWidget(placeholder)
            return

        for insight in insights:
            self._cards_container.addWidget(self._make_card(insight))

    def _make_card(self, insight: dict) -> QFrame:
        style = _SEVERITY_STYLES.get(insight["severity"], _SEVERITY_STYLES["info"])

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: {style['bg']}; border: 1px solid {style['border']};"
            f" border-left: 4px solid {style['border']}; border-radius: 8px; }}"
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 14)
        layout.setSpacing(6)

        # Title row with badge
        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        badge = QLabel(style["badge"])
        badge.setStyleSheet(
            f"background: {style['badge_bg']}; color: {style['badge_text']}; font-size: 9px;"
            f" font-weight: 700; padding: 2px 7px; border-radius: 3px;"
        )
        badge.setFixedHeight(18)

        title_lbl = QLabel(insight["title"])
        title_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #1D1D1F;")

        title_row.addWidget(badge)
        title_row.addWidget(title_lbl)
        title_row.addStretch()
        layout.addLayout(title_row)

        body = QLabel(insight["body"])
        body.setWordWrap(True)
        body.setStyleSheet("font-size: 12px; color: #1D1D1F; line-height: 1.5;")
        layout.addWidget(body)

        return card
