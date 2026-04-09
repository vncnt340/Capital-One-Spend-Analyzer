from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel


class MetricCard(QFrame):
    """A white card showing a label and a large value."""

    def __init__(self, label: str, value: str = "—", accent: str | None = None,
                 parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumWidth(140)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        self._label_w = QLabel(label.upper())
        self._label_w.setObjectName("metric_label")

        self._value_w = QLabel(value)
        self._value_w.setObjectName("metric_value")
        self._value_w.setStyleSheet(
            f"font-size: 26px; font-weight: 700; color: {accent if accent else '#111827'};"
        )

        self._subtitle_w = QLabel("")
        self._subtitle_w.setStyleSheet("font-size: 10px; color: #6B7280;")
        self._subtitle_w.setWordWrap(True)
        self._subtitle_w.hide()

        layout.addWidget(self._label_w)
        layout.addWidget(self._value_w)
        layout.addWidget(self._subtitle_w)

    def set_value(self, value: str, accent: str | None = None) -> None:
        self._value_w.setText(value)
        self._value_w.setStyleSheet(
            f"font-size: 26px; font-weight: 700; color: {accent if accent else '#111827'};"
        )

    def set_subtitle(self, text: str) -> None:
        self._subtitle_w.setText(text)
        self._subtitle_w.setVisible(bool(text))
