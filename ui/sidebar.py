from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPainterPath
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton
)

from ui.theme import SIDEBAR_BG, SIDEBAR_TEXT, ACCENT


NAV_ITEMS = [
    ("Overview", "overview"),
    ("Insights", "insights"),
    ("Categories", "categories"),
    ("Merchants", "merchants"),
    ("Subscriptions", "subscriptions"),
    ("Trends", "trends"),
    ("Tagging Rules", "tagging_rules"),
]

_EXPANDED_WIDTH = 200
_COLLAPSED_WIDTH = 48


class Sidebar(QWidget):
    page_selected = pyqtSignal(int)
    import_requested = pyqtSignal()

    _RADIUS = 16

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._collapsed = False
        self.setFixedWidth(_EXPANDED_WIDTH)
        self._build_ui()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        r = self.rect()
        rad = self._RADIUS
        # Rounded bottom corners only
        path.moveTo(r.left(), r.top())
        path.lineTo(r.right(), r.top())
        path.lineTo(r.right(), r.bottom() - rad)
        path.quadTo(r.right(), r.bottom(), r.right() - rad, r.bottom())
        path.lineTo(r.left() + rad, r.bottom())
        path.quadTo(r.left(), r.bottom(), r.left(), r.bottom() - rad)
        path.lineTo(r.left(), r.top())
        path.closeSubpath()
        painter.fillPath(path, QColor(SIDEBAR_BG))
        painter.end()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header with app name + collapse button
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 16, 8, 16)
        header_layout.setSpacing(0)

        self._app_name = QLabel("Spend\nAnalyzer")
        self._app_name.setStyleSheet(
            "color: white; font-size: 18px; font-weight: 700;"
        )
        header_layout.addWidget(self._app_name, 1)

        self._collapse_btn = QPushButton("◀")
        self._collapse_btn.setFixedSize(32, 32)
        self._collapse_btn.setToolTip("Collapse sidebar")
        self._collapse_btn.setStyleSheet(
            "QPushButton { background: #2C2C2E; border: none; color: #FFFFFF;"
            " font-size: 14px; border-radius: 6px; font-weight: bold; }"
            "QPushButton:hover { background: #3A3A3C; border: none; color: #FFFFFF; }"
            "QPushButton:pressed { background: #48484A; border: none; color: #FFFFFF; }"
        )
        self._collapse_btn.clicked.connect(self.toggle_collapsed)
        header_layout.addWidget(self._collapse_btn)

        layout.addWidget(header)

        # Nav list
        self._nav = QListWidget()
        self._nav.setObjectName("nav")
        for label, _ in NAV_ITEMS:
            item = QListWidgetItem(label)
            item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter)
            self._nav.addItem(item)
        self._nav.setCurrentRow(0)
        self._nav.currentRowChanged.connect(self.page_selected)
        self._nav.setSizePolicy(self._nav.sizePolicy().horizontalPolicy(),
                                self._nav.sizePolicy().verticalPolicy())
        self._nav.setMaximumHeight(len(NAV_ITEMS) * 44 + 16)
        layout.addWidget(self._nav)

        # Import button — directly below nav, no stretch
        self._import_container = QWidget()
        import_layout = QVBoxLayout(self._import_container)
        import_layout.setContentsMargins(12, 12, 12, 4)

        self._import_btn = QPushButton("Import CSV")
        self._import_btn.setObjectName("import_btn")
        self._import_btn.setStyleSheet(
            "QPushButton { background: #4F7EF7; color: #FFFFFF; font-weight: 600;"
            " border: none; border-radius: 16px; padding: 9px 16px; font-size: 13px; }"
            "QPushButton:hover { background: #3D6EE0; color: #FFFFFF; }"
        )
        self._import_btn.clicked.connect(self.import_requested)
        import_layout.addWidget(self._import_btn)
        layout.addWidget(self._import_container)

        # File name label
        self._file_label = QLabel("")
        self._file_label.setStyleSheet(
            f"color: {SIDEBAR_TEXT}; font-size: 10px; padding: 0 12px 8px 12px;"
        )
        self._file_label.setWordWrap(True)
        layout.addWidget(self._file_label)

        layout.addStretch()

    def toggle_collapsed(self) -> None:
        self._collapsed = not self._collapsed
        if self._collapsed:
            self.setFixedWidth(_COLLAPSED_WIDTH)
            self._app_name.hide()
            self._nav.hide()
            self._import_container.hide()
            self._file_label.hide()
            self._collapse_btn.setText("▶")
            self._collapse_btn.setToolTip("Expand sidebar")
        else:
            self.setFixedWidth(_EXPANDED_WIDTH)
            self._app_name.show()
            self._nav.show()
            self._import_container.show()
            self._file_label.show()
            self._collapse_btn.setText("◀")
            self._collapse_btn.setToolTip("Collapse sidebar")

    def set_file_label(self, filename: str) -> None:
        self._file_label.setText(filename)

    def select_page(self, index: int) -> None:
        self._nav.setCurrentRow(index)
