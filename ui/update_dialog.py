from __future__ import annotations

import subprocess
import threading
import urllib.request
import tempfile
import os

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar
)

from ui.theme import ACCENT, TEXT_PRIMARY, TEXT_SECONDARY


class _DownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)  # path to downloaded file
    error = pyqtSignal(str)

    def __init__(self, url: str) -> None:
        super().__init__()
        self._url = url

    def run(self) -> None:
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".dmg", delete=False)
            tmp.close()

            def reporthook(count, block_size, total_size):
                if total_size > 0:
                    pct = min(int(count * block_size * 100 / total_size), 100)
                    self.progress.emit(pct)

            urllib.request.urlretrieve(self._url, tmp.name, reporthook)
            self.finished.emit(tmp.name)
        except Exception as e:
            self.error.emit(str(e))


class UpdateDialog(QDialog):
    def __init__(self, update_info: dict, parent=None) -> None:
        super().__init__(parent)
        self._info = update_info
        self._thread: _DownloadThread | None = None
        self.setWindowTitle("Update Available")
        self.setMinimumWidth(420)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title = QLabel(f"SpendAnalyzer {self._info['version']} is available")
        title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {TEXT_PRIMARY};")
        layout.addWidget(title)

        subtitle = QLabel("A new version is available on GitHub. Would you like to update?")
        subtitle.setStyleSheet(f"font-size: 13px; color: {TEXT_SECONDARY};")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setFixedHeight(6)
        self._progress.setTextVisible(False)
        self._progress.setStyleSheet(
            f"QProgressBar {{ background: #EEEEEE; border-radius: 3px; border: none; }}"
            f"QProgressBar::chunk {{ background: {ACCENT}; border-radius: 3px; }}"
        )
        self._progress.hide()
        layout.addWidget(self._progress)

        self._status = QLabel("")
        self._status.setStyleSheet(f"font-size: 11px; color: {TEXT_SECONDARY};")
        self._status.hide()
        layout.addWidget(self._status)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self._skip_btn = QPushButton("Skip")
        self._skip_btn.setStyleSheet(
            "QPushButton { background: #EEEEEE; color: #000000; border: none;"
            " border-radius: 8px; padding: 9px 20px; font-size: 13px; }"
            "QPushButton:hover { background: #D2D2D7; }"
        )
        self._skip_btn.clicked.connect(self.reject)

        self._update_btn = QPushButton("Download & Install")
        self._update_btn.setStyleSheet(
            f"QPushButton {{ background: {ACCENT}; color: #FFFFFF; border: none;"
            f" border-radius: 8px; padding: 9px 20px; font-size: 13px; font-weight: 600; }}"
            f"QPushButton:hover {{ background: #0077CC; color: #FFFFFF; }}"
            f"QPushButton:disabled {{ background: #979797; color: #FFFFFF; }}"
        )
        self._update_btn.clicked.connect(self._start_download)

        btn_row.addStretch()
        btn_row.addWidget(self._skip_btn)
        btn_row.addWidget(self._update_btn)
        layout.addLayout(btn_row)

    def _start_download(self) -> None:
        download_url = self._info.get("download_url", "")
        if not download_url:
            # No DMG asset — open release page in browser
            subprocess.Popen(["open", self._info["release_url"]])
            self.accept()
            return

        self._update_btn.setEnabled(False)
        self._skip_btn.setEnabled(False)
        self._update_btn.setText("Downloading…")
        self._progress.show()
        self._status.show()
        self._status.setText("Downloading update…")

        self._thread = _DownloadThread(download_url)
        self._thread.progress.connect(self._progress.setValue)
        self._thread.finished.connect(self._on_downloaded)
        self._thread.error.connect(self._on_error)
        self._thread.start()

    def _on_downloaded(self, path: str) -> None:
        self._status.setText("Opening installer…")
        subprocess.Popen(["open", path])
        self.accept()

    def _on_error(self, msg: str) -> None:
        self._status.setText(f"Download failed: {msg}")
        self._update_btn.setEnabled(True)
        self._skip_btn.setEnabled(True)
        self._update_btn.setText("Download & Install")
        self._progress.hide()
