from __future__ import annotations

import re

from PyQt6.QtCore import Qt, QSortFilterProxyModel, QAbstractTableModel, QModelIndex, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableView, QHeaderView, QAbstractItemView, QMenu, QApplication,
)


_NUMERIC_RE = re.compile(r"^-?\$?[\d,]+(\.\d+)?$")


def _parse_numeric(val: str) -> float | None:
    """Return float if val looks like a number or currency, else None."""
    cleaned = val.strip().replace(",", "").replace("$", "")
    if _NUMERIC_RE.match(val.strip()):
        try:
            return float(cleaned)
        except ValueError:
            pass
    return None


class _TableModel(QAbstractTableModel):
    def __init__(self, columns: list[str]) -> None:
        super().__init__()
        self._columns = columns
        self._rows: list[list[str]] = []
        self._alignments: list[Qt.AlignmentFlag] = []
        self._row_colors: list[str | None] = []      # per-row foreground hex or None
        self._row_backgrounds: list[str | None] = [] # per-row background hex or None
        self._row_bold: list[bool] = []               # per-row bold flag

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._columns)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return self._rows[index.row()][index.column()]
        if role == Qt.ItemDataRole.TextAlignmentRole:
            if self._alignments and index.column() < len(self._alignments):
                return int(self._alignments[index.column()])
            return int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        if role == Qt.ItemDataRole.ForegroundRole:
            from PyQt6.QtGui import QColor
            if self._row_colors and index.row() < len(self._row_colors):
                color = self._row_colors[index.row()]
                if color:
                    return QColor(color)
        if role == Qt.ItemDataRole.BackgroundRole:
            from PyQt6.QtGui import QColor
            if self._row_backgrounds and index.row() < len(self._row_backgrounds):
                bg = self._row_backgrounds[index.row()]
                if bg:
                    return QColor(bg)
        if role == Qt.ItemDataRole.FontRole:
            from PyQt6.QtGui import QFont
            if self._row_bold and index.row() < len(self._row_bold) and self._row_bold[index.row()]:
                f = QFont()
                f.setBold(True)
                return f
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._columns[section]
        return None

    def load(self, rows: list[list[str]], alignments: list[Qt.AlignmentFlag] | None = None,
             row_colors: list[str | None] | None = None,
             row_backgrounds: list[str | None] | None = None,
             row_bold: list[bool] | None = None) -> None:
        self.beginResetModel()
        self._rows = rows
        self._alignments = alignments or []
        self._row_colors = row_colors or []
        self._row_backgrounds = row_backgrounds or []
        self._row_bold = row_bold or []
        self.endResetModel()


class _MultiColumnProxy(QSortFilterProxyModel):
    """Filters rows by matching each column's filter string against that column."""

    def __init__(self) -> None:
        super().__init__()
        self._col_filters: list[str] = []

    def set_col_filters(self, filters: list[str]) -> None:
        self._col_filters = [f.lower() for f in filters]
        self.invalidateFilter()

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        l_val = self.sourceModel().data(left, Qt.ItemDataRole.DisplayRole) or ""
        r_val = self.sourceModel().data(right, Qt.ItemDataRole.DisplayRole) or ""
        l_num = _parse_numeric(l_val)
        r_num = _parse_numeric(r_val)
        if l_num is not None and r_num is not None:
            return l_num < r_num
        return str(l_val).lower() < str(r_val).lower()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        for col, ftext in enumerate(self._col_filters):
            if not ftext:
                continue
            idx = self.sourceModel().index(source_row, col, source_parent)
            val = self.sourceModel().data(idx, Qt.ItemDataRole.DisplayRole) or ""
            if ftext not in str(val).lower():
                return False
        return True


# Rebuild SortableTable to use _MultiColumnProxy
class SortableTable(QWidget):
    row_clicked = pyqtSignal(int)
    filter_changed = pyqtSignal()

    def __init__(self, columns: list[str], parent=None) -> None:
        super().__init__(parent)
        self._columns = columns
        self._model = _TableModel(columns)
        self._proxy = _MultiColumnProxy()
        self._proxy.setSourceModel(self._model)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Filter bar — filters are children of this container and positioned manually
        self._filter_bar = QWidget()
        self._filter_bar.setFixedHeight(30)
        self._filters: list[QLineEdit] = []

        for col_name in self._columns:
            f = QLineEdit(self._filter_bar)
            f.setPlaceholderText("Filter…")
            f.setFixedHeight(26)
            f.setStyleSheet("color: #111827; background: #FFFFFF; border: 1px solid #E2E6EE; border-radius: 4px; padding: 2px 6px; font-size: 11px;")
            f.textChanged.connect(self._apply_filters)
            self._filters.append(f)

        self._reset_btn = QPushButton("✕ Reset", self._filter_bar)
        self._reset_btn.setFixedSize(64, 26)
        self._reset_btn.setStyleSheet(
            "QPushButton { color: #6B7280; background: #F3F4F6; border: 1px solid #E2E6EE; "
            "border-radius: 4px; font-size: 11px; padding: 0 6px; }"
            "QPushButton:hover { background: #E5E7EB; color: #111827; }"
        )
        self._reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._reset_btn.hide()
        self._reset_btn.clicked.connect(self.reset_filters)

        layout.addWidget(self._filter_bar)

        self._view = QTableView()
        self._view.setModel(self._proxy)
        self._view.setSortingEnabled(True)
        self._view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._view.setAlternatingRowColors(True)
        self._view.verticalHeader().setVisible(False)
        header = self._view.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.sectionResized.connect(self._sync_filters)
        header.geometriesChanged.connect(self._sync_filters)
        self._view.setShowGrid(True)
        self._view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._view.customContextMenuRequested.connect(self._show_context_menu)
        self._view.clicked.connect(self._on_clicked)

        copy_action = QAction("Copy", self._view)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(self._copy_selected_rows)
        self._view.addAction(copy_action)

        layout.addWidget(self._view)

    _RESET_BTN_W = 68  # width reserved for reset button

    def _sync_filters(self) -> None:
        header = self._view.horizontalHeader()
        any_active = any(f.text() for f in self._filters)
        self._reset_btn.setVisible(any_active)
        reserve = self._RESET_BTN_W if any_active else 0
        x = 0
        for i, f in enumerate(self._filters):
            w = header.sectionSize(i)
            # shrink last column's filter to leave room for reset button
            draw_w = max(0, w - 2 - (reserve if i == len(self._filters) - 1 else 0))
            f.setGeometry(x, 2, draw_w, 26)
            x += w
        if any_active:
            self._reset_btn.move(x - self._RESET_BTN_W, 2)

    def _apply_filters(self) -> None:
        self._proxy.set_col_filters([f.text() for f in self._filters])
        self._sync_filters()
        self.filter_changed.emit()

    def reset_filters(self) -> None:
        for f in self._filters:
            f.blockSignals(True)
            f.clear()
            f.blockSignals(False)
        self._proxy.set_col_filters([""] * len(self._filters))
        self._sync_filters()
        self.filter_changed.emit()

    def _show_context_menu(self, pos) -> None:
        index = self._view.indexAt(pos)
        menu = QMenu(self._view)

        if index.isValid():
            copy_cell = QAction("Copy Cell", menu)
            copy_cell.triggered.connect(lambda: self._copy_cell(index))
            menu.addAction(copy_cell)

            copy_row = QAction("Copy Row", menu)
            copy_row.triggered.connect(self._copy_selected_rows)
            menu.addAction(copy_row)

            menu.addSeparator()

        copy_all = QAction("Copy All (visible)", menu)
        copy_all.triggered.connect(self._copy_all_visible)
        menu.addAction(copy_all)

        menu.exec(self._view.viewport().mapToGlobal(pos))

    def _copy_cell(self, index: QModelIndex) -> None:
        text = self._proxy.data(index, Qt.ItemDataRole.DisplayRole) or ""
        QApplication.clipboard().setText(str(text))

    def _copy_selected_rows(self) -> None:
        rows = self._view.selectionModel().selectedRows()
        if not rows:
            return
        lines = []
        for proxy_row in sorted(r.row() for r in rows):
            line = "\t".join(
                str(self._proxy.data(self._proxy.index(proxy_row, c), Qt.ItemDataRole.DisplayRole) or "")
                for c in range(self._proxy.columnCount())
            )
            lines.append(line)
        QApplication.clipboard().setText("\n".join(lines))

    def _copy_all_visible(self) -> None:
        header = "\t".join(self._columns)
        lines = [header]
        for r in range(self._proxy.rowCount()):
            line = "\t".join(
                str(self._proxy.data(self._proxy.index(r, c), Qt.ItemDataRole.DisplayRole) or "")
                for c in range(self._proxy.columnCount())
            )
            lines.append(line)
        QApplication.clipboard().setText("\n".join(lines))

    def _on_clicked(self, index: QModelIndex) -> None:
        source_row = self._proxy.mapToSource(index).row()
        self.row_clicked.emit(source_row)

    _SPEND_COLS = {"net spend", "total spend", "amount", "net"}

    def populate(self, rows: list[list], alignments: list[Qt.AlignmentFlag] | None = None,
                 row_colors: list[str | None] | None = None,
                 row_backgrounds: list[str | None] | None = None,
                 row_bold: list[bool] | None = None) -> None:
        self._model.load([[str(v) for v in row] for row in rows], alignments, row_colors,
                         row_backgrounds, row_bold)
        self._view.resizeColumnsToContents()
        self._sync_filters()
        for f in self._filters:
            f.blockSignals(True)
            f.clear()
            f.blockSignals(False)
        # Auto-sort by spend column descending
        for i, col in enumerate(self._columns):
            if col.lower() in self._SPEND_COLS:
                self._view.sortByColumn(i, Qt.SortOrder.DescendingOrder)
                break

    def item(self, row: int, col: int):
        proxy_index = self._proxy.index(row, col)
        val = self._proxy.data(proxy_index, Qt.ItemDataRole.DisplayRole)

        class _Item:
            def __init__(self, t): self._t = t
            def text(self): return self._t or ""

        return _Item(val)

    def visible_values(self, col: int) -> list[str]:
        """Return all visible values in a column after filtering."""
        return [
            str(self._proxy.data(self._proxy.index(r, col), Qt.ItemDataRole.DisplayRole) or "")
            for r in range(self._proxy.rowCount())
        ]

    def rowCount(self) -> int:
        return self._proxy.rowCount()

    def columnCount(self) -> int:
        return self._proxy.columnCount()
