from __future__ import annotations

from typing import Callable

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from ui.theme import CHART_BG, CONTENT_BG


class ChartCanvas(QWidget):
    """
    Reusable matplotlib-in-Qt widget.

    Usage:
        canvas = ChartCanvas(self, figsize=(8, 4))
        canvas.update_figure(lambda fig: _draw(fig))
    """

    def __init__(self, parent: QWidget | None = None, figsize: tuple = (8, 4)) -> None:
        super().__init__(parent)
        self._fig = Figure(figsize=figsize, dpi=100, facecolor=CHART_BG)
        self._canvas = FigureCanvasQTAgg(self._fig)
        self._canvas.setStyleSheet(f"background: {CHART_BG};")
        self._canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._canvas.setMinimumSize(1, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._canvas)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def update_figure(self, draw_fn: Callable[[Figure], None]) -> None:
        """Clear the figure, call draw_fn to populate it, then redraw."""
        self._fig.clf()
        try:
            draw_fn(self._fig)
            self._fig.tight_layout(pad=1.5)
        except Exception:
            ax = self._fig.add_subplot(111)
            ax.text(0.5, 0.5, "No data to display", ha="center", va="center",
                    color="#9CA3AF", fontsize=13, transform=ax.transAxes)
            ax.axis("off")
        self._canvas.draw_idle()

    def clear(self) -> None:
        self._fig.clf()
        ax = self._fig.add_subplot(111)
        ax.axis("off")
        self._canvas.draw_idle()
