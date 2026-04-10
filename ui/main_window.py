from __future__ import annotations

import os
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QStackedWidget,
    QFileDialog, QMessageBox, QLabel
)
from PyQt6.QtGui import QAction, QKeySequence

import traceback

from core.loader import LoaderError
from core.store import AppStore
from ui.sidebar import Sidebar
from ui.theme import CONTENT_BG


class MainWindow(QMainWindow):
    def __init__(self, store: AppStore) -> None:
        super().__init__()
        self._store = store
        self._pages: dict[int, QWidget | None] = {i: None for i in range(7)}

        self.setWindowTitle("Spend Analyzer")
        self.setMinimumSize(1100, 700)
        self.resize(1300, 800)

        self._build_menu()
        self._build_ui()

    def _build_menu(self) -> None:
        menu = self.menuBar()

        view_menu = menu.addMenu("View")
        toggle_action = QAction("Toggle Sidebar", self)
        toggle_action.setShortcut(QKeySequence("Ctrl+\\"))
        toggle_action.triggered.connect(self._toggle_sidebar)
        view_menu.addAction(toggle_action)

        file_menu = menu.addMenu("File")

        import_action = QAction("Import CSV…", self)
        import_action.setShortcut(QKeySequence("Ctrl+O"))
        import_action.triggered.connect(self._import_csv)
        file_menu.addAction(import_action)

        file_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        self._sidebar = Sidebar()
        self._sidebar.page_selected.connect(self._show_page)
        self._sidebar.import_requested.connect(self._import_csv)
        layout.addWidget(self._sidebar)

        # Stack
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background: {CONTENT_BG};")

        # Placeholder for each page slot
        for _ in range(7):
            placeholder = QWidget()
            self._stack.addWidget(placeholder)

        layout.addWidget(self._stack, 1)

        # Load first page immediately
        self._show_page(0)

    def _toggle_sidebar(self) -> None:
        self._sidebar.toggle_collapsed()

    def _show_page(self, index: int) -> None:
        if self._pages[index] is None:
            self._pages[index] = self._make_page(index)
            self._stack.removeWidget(self._stack.widget(index))
            self._stack.insertWidget(index, self._pages[index])

        self._stack.setCurrentIndex(index)
        # Trigger canvas redraw on switch
        page = self._pages[index]
        if page and hasattr(page, "refresh"):
            if self._store.is_loaded:
                page.refresh()

    def _make_page(self, index: int) -> QWidget:
        from ui.pages.overview_page import OverviewPage
        from ui.pages.insights_page import InsightsPage
        from ui.pages.categories_page import CategoriesPage
        from ui.pages.merchants_page import MerchantsPage
        from ui.pages.subscriptions_page import SubscriptionsPage
        from ui.pages.trends_page import TrendsPage
        from ui.pages.tagging_rules_page import TaggingRulesPage

        pages = [
            lambda: OverviewPage(self._store),
            lambda: InsightsPage(self._store),
            lambda: CategoriesPage(self._store),
            lambda: MerchantsPage(self._store),
            lambda: SubscriptionsPage(self._store),
            lambda: TrendsPage(self._store),
            lambda: TaggingRulesPage(self._store),
        ]
        return pages[index]()

    def _import_csv(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Capital One CSV",
            str(Path.home() / "Downloads"),
            "CSV Files (*.csv);;All Files (*)",
        )
        if not path:
            return

        try:
            self._store.load_csv(path)
        except LoaderError as e:
            QMessageBox.critical(self, "Import Failed", str(e))
            return
        except Exception:
            QMessageBox.critical(self, "Import Failed",
                                 f"Unexpected error loading CSV:\n\n{traceback.format_exc()}")
            return

        filename = os.path.basename(path)
        self._sidebar.set_file_label(filename)

        # Force refresh of current page
        current = self._stack.currentIndex()
        page = self._pages[current]
        if page and hasattr(page, "refresh"):
            page.refresh()
