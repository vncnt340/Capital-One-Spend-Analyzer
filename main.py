import sys
import matplotlib
matplotlib.use("QtAgg")  # Must be set before any other matplotlib imports
import matplotlib.pyplot as plt
plt.rcParams.update({
    "font.weight": "bold",
    "axes.titleweight": "bold",
    "axes.labelweight": "bold",
    "axes.labelcolor": "#666666",
    "xtick.color": "#666666",
    "ytick.color": "#666666",
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "figure.facecolor": "#FFFFFF",
    "axes.facecolor": "#FFFFFF",
    "grid.color": "#EEEEEE",
    "axes.spines.top": False,
    "axes.spines.right": False,
})

import threading
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication

from core.store import AppStore
from core.updater import check_for_update
from ui.main_window import MainWindow
from ui.theme import app_stylesheet
from ui.update_dialog import UpdateDialog
from version import __version__, GITHUB_REPO


def _check_update_async(window: MainWindow) -> None:
    """Run update check in background thread; show dialog on main thread if update found."""
    info = check_for_update(GITHUB_REPO, __version__)
    if info:
        QTimer.singleShot(0, lambda: UpdateDialog(info, window).exec())


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("SpendAnalyzer")
    app.setOrganizationName("SpendAnalyzer")
    app.setStyleSheet(app_stylesheet())

    store = AppStore()
    window = MainWindow(store)
    window.show()

    # Check for updates in background after a short delay
    QTimer.singleShot(2000, lambda: threading.Thread(
        target=_check_update_async, args=(window,), daemon=True
    ).start())

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
