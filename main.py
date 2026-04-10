import sys
import os

# macOS: set QT_CONF_PATH before importing PyQt6 to prevent a crash when the app
# is Gatekeeper-translocated (runs from /private/var/folders/ as Background proc).
# Qt's Darwin permission plugins are baked into QtCore.abi3.so as static
# initializers; they call QLibraryInfoPrivate::paths() → CFBundleGetMainBundle(),
# which returns NULL in the translocated context → SIGSEGV at 0x8.
# Setting QT_CONF_PATH gives Qt the prefix/plugin paths via getenv() before the
# initializer runs, so it returns early without ever touching CFBundle.
if sys.platform == "darwin":
    try:
        _exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        _contents = os.path.dirname(_exe_dir)  # .app/Contents/
        _qt_conf = os.path.join(_contents, "Resources", "qt.conf")
        if os.path.exists(_qt_conf):
            os.environ.setdefault("QT_CONF_PATH", _qt_conf)
    except Exception:
        pass

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

import traceback
import threading
from PyQt6.QtCore import Qt, QTimer, QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMessageBox

from core.store import AppStore
from core.updater import check_for_update
from ui.main_window import MainWindow
from ui.theme import app_stylesheet
from ui.update_dialog import UpdateDialog
from version import __version__, GITHUB_REPO


class _App(QApplication):
    """QApplication subclass that catches Python exceptions in Qt slots/events
    and shows them as error dialogs instead of calling abort()."""

    def notify(self, receiver, event):
        try:
            return super().notify(receiver, event)
        except Exception:
            msg = traceback.format_exc()
            dlg = QMessageBox()
            dlg.setWindowTitle("Unexpected Error")
            dlg.setText("An error occurred. The app will continue running.")
            dlg.setDetailedText(msg)
            dlg.setIcon(QMessageBox.Icon.Critical)
            dlg.exec()
            return False


class _UpdateSignal(QObject):
    found = pyqtSignal(dict)


def main() -> None:
    app = _App(sys.argv)
    app.setApplicationName("SpendAnalyzer")
    app.setOrganizationName("SpendAnalyzer")
    app.setStyleSheet(app_stylesheet())

    store = AppStore()
    window = MainWindow(store)
    window.show()

    # Check for updates in background — use a signal so the dialog is
    # shown on the main thread (QTimer.singleShot from a non-main thread
    # is not thread-safe and silently does nothing in PyQt6).
    _update_sig = _UpdateSignal()
    _update_sig.found.connect(lambda info: UpdateDialog(info, window).exec())

    def _check():
        info = check_for_update(GITHUB_REPO, __version__)
        if info:
            _update_sig.found.emit(info)

    QTimer.singleShot(2000, lambda: threading.Thread(target=_check, daemon=True).start())

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
