from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QCheckBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFrame
)

from core.store import AppStore
from ui.theme import ACCENT, RED, TEXT_SECONDARY


class TaggingRulesPage(QWidget):
    def __init__(self, store: AppStore, parent=None) -> None:
        super().__init__(parent)
        self._store = store
        self._build_ui()
        store.rules_changed.connect(self._refresh_table)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title = QLabel("Tagging Rules")
        title.setObjectName("page_title")
        layout.addWidget(title)

        subtitle = QLabel(
            "Rules are applied in order — first match wins. "
            "Keywords match against the raw transaction description."
        )
        subtitle.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(subtitle)

        # ── Add rule form ─────────────────────────────────────────────────────
        form_frame = QFrame()
        form_frame.setObjectName("card")
        form_layout = QHBoxLayout(form_frame)
        form_layout.setContentsMargins(16, 12, 16, 12)
        form_layout.setSpacing(10)

        self._kw_input = QLineEdit()
        self._kw_input.setPlaceholderText("Keyword (e.g. STARBUCKS)")
        self._kw_input.setMinimumWidth(200)

        self._subcat_input = QLineEdit()
        self._subcat_input.setPlaceholderText("Sub-category (e.g. Coffee)")
        self._subcat_input.setMinimumWidth(180)

        self._case_check = QCheckBox("Case sensitive")

        self._add_btn = QPushButton("Add Rule")
        self._add_btn.setObjectName("import_btn")
        self._add_btn.setStyleSheet("QPushButton { background: #4F7EF7; color: #FFFFFF; font-weight: 600; border: none; border-radius: 8px; padding: 9px 16px; font-size: 13px; } QPushButton:hover { background: #3D6EE0; color: #FFFFFF; }")
        self._add_btn.clicked.connect(self._add_rule)
        self._kw_input.returnPressed.connect(self._add_rule)
        self._subcat_input.returnPressed.connect(self._add_rule)

        form_layout.addWidget(QLabel("Keyword:"))
        form_layout.addWidget(self._kw_input)
        form_layout.addWidget(QLabel("→  Sub-category:"))
        form_layout.addWidget(self._subcat_input)
        form_layout.addWidget(self._case_check)
        form_layout.addWidget(self._add_btn)
        form_layout.addStretch()
        layout.addWidget(form_frame)

        # ── Rules table ───────────────────────────────────────────────────────
        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["Keyword", "Sub-category", "Case Sensitive", "Actions"])
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table)

        # Hint
        hint = QLabel(
            "Tip: rules are saved automatically to ~/Library/Application Support/SpendAnalyzer/rules.json"
        )
        hint.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(hint)

        self._refresh_table()

    def _refresh_table(self) -> None:
        rules = self._store.rules
        self._table.setRowCount(0)

        CENTER = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter

        for i, rule in enumerate(rules):
            row = self._table.rowCount()
            self._table.insertRow(row)

            kw_item = QTableWidgetItem(rule["keyword"])
            kw_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 0, kw_item)

            sc_item = QTableWidgetItem(rule["sub_category"])
            sc_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 1, sc_item)

            cs_item = QTableWidgetItem("Yes" if rule.get("match_case") else "No")
            cs_item.setTextAlignment(CENTER)
            self._table.setItem(row, 2, cs_item)

            # Actions cell
            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)

            _btn_style = (
                "QPushButton { background: #F5F5F7; color: #1D1D1F; border: 1px solid #D2D2D7;"
                " border-radius: 4px; padding: 2px 6px; font-size: 12px; }"
                "QPushButton:hover { background: #D2D2D7; color: #1D1D1F; }"
            )
            _del_style = (
                "QPushButton { background: #FEF2F2; color: #DC2626; border: 1px solid #FECACA;"
                " border-radius: 4px; padding: 2px 10px; font-size: 12px; }"
                "QPushButton:hover { background: #FEE2E2; color: #DC2626; }"
            )

            up_btn = QPushButton("↑")
            up_btn.setFixedSize(28, 26)
            up_btn.setStyleSheet(_btn_style)
            up_btn.clicked.connect(lambda _, idx=i: self._store.move_rule(idx, -1))

            down_btn = QPushButton("↓")
            down_btn.setFixedSize(28, 26)
            down_btn.setStyleSheet(_btn_style)
            down_btn.clicked.connect(lambda _, idx=i: self._store.move_rule(idx, 1))

            del_btn = QPushButton("Delete")
            del_btn.setFixedHeight(26)
            del_btn.setMinimumWidth(58)
            del_btn.setStyleSheet(_del_style)
            del_btn.clicked.connect(lambda _, idx=i: self._delete_rule(idx))

            actions_layout.addWidget(up_btn)
            actions_layout.addWidget(down_btn)
            actions_layout.addWidget(del_btn)
            actions_layout.addStretch()
            self._table.setCellWidget(row, 3, actions)
            self._table.setRowHeight(row, 40)

        self._table.resizeColumnsToContents()

    def _add_rule(self) -> None:
        keyword = self._kw_input.text().strip()
        sub_category = self._subcat_input.text().strip()
        if not keyword or not sub_category:
            return
        match_case = self._case_check.isChecked()
        self._store.add_rule(keyword, sub_category, match_case)
        self._kw_input.clear()
        self._subcat_input.clear()
        self._kw_input.setFocus()

    def _delete_rule(self, index: int) -> None:
        rules = self._store.rules
        if index >= len(rules):
            return
        rule = rules[index]
        reply = QMessageBox.question(
            self, "Delete Rule",
            f'Delete rule "{rule["keyword"]} → {rule["sub_category"]}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._store.delete_rule(index)
