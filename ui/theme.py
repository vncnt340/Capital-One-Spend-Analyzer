from __future__ import annotations

# ── Apple-inspired Palette ────────────────────────────────────────────────────
SIDEBAR_BG = "#1D1D1F"
SIDEBAR_TEXT = "#8E8E93"
SIDEBAR_SELECTED_BG = "#2C2C2E"
SIDEBAR_SELECTED_TEXT = "#FFFFFF"
SIDEBAR_HOVER_BG = "#242426"

CONTENT_BG = "#F5F5F7"
CARD_BG = "#FFFFFF"
CARD_BORDER = "#D2D2D7"

ACCENT = "#0088CC"
ACCENT_LIGHT = "#E0F2FC"
GREEN = "#34C759"
RED = "#FF3B30"
ORANGE = "#FF9500"
PURPLE = "#AF52DE"

TEXT_PRIMARY = "#000000"
TEXT_SECONDARY = "#666666"
TEXT_MUTED = "#979797"

# ── Chart colors ──────────────────────────────────────────────────────────────
CHART_COLORS = [
    "#0088CC", "#666666", "#979797", "#000000",
    "#33AADD", "#4DA6CC", "#2277AA", "#888888",
    "#BBBBBB", "#005588",
]

CHART_BG = "#FFFFFF"
CHART_GRID = "#EEEEEE"


# ── Stylesheet ────────────────────────────────────────────────────────────────
def app_stylesheet() -> str:
    return f"""
    QMainWindow, QWidget#central {{
        background: {CONTENT_BG};
    }}
    QWidget#sidebar {{
        background: transparent;
    }}
    QListWidget#nav {{
        background: {SIDEBAR_BG};
        border: none;
        outline: none;
        padding: 8px 0;
        font-size: 13px;
    }}
    QListWidget#nav::item {{
        color: {SIDEBAR_TEXT};
        padding: 10px 20px;
        border-radius: 8px;
        margin: 1px 8px;
    }}
    QListWidget#nav::item:selected {{
        background: {SIDEBAR_SELECTED_BG};
        color: {SIDEBAR_SELECTED_TEXT};
    }}
    QListWidget#nav::item:hover:!selected {{
        background: {SIDEBAR_HOVER_BG};
        color: {SIDEBAR_SELECTED_TEXT};
    }}
    QPushButton#import_btn {{
        background: {ACCENT};
        color: #FFFFFF;
        border: none;
        border-radius: 980px;
        padding: 9px 16px;
        font-size: 13px;
        font-weight: 600;
    }}
    QPushButton#import_btn:hover {{
        background: #0077ED;
        color: #FFFFFF;
    }}
    QPushButton#import_btn:pressed {{
        background: #006CDC;
        color: #FFFFFF;
    }}
    QPushButton {{
        background: {CARD_BG};
        color: {TEXT_PRIMARY};
        border: 1px solid {CARD_BORDER};
        border-radius: 8px;
        padding: 6px 14px;
        font-size: 12px;
    }}
    QPushButton:hover {{
        background: {ACCENT_LIGHT};
        border-color: {ACCENT};
        color: {ACCENT};
    }}
    QPushButton#danger {{
        color: {RED};
        border-color: {RED};
    }}
    QPushButton#danger:hover {{
        background: #FFF2F0;
    }}
    QTableWidget, QTableView {{
        background: {CARD_BG};
        border: 1px solid {CARD_BORDER};
        border-radius: 12px;
        gridline-color: {CARD_BORDER};
        font-size: 12px;
        color: {TEXT_PRIMARY};
        selection-background-color: {ACCENT_LIGHT};
        selection-color: {TEXT_PRIMARY};
        outline: none;
    }}
    QTableWidget::item, QTableView::item {{
        padding: 6px 10px;
        color: {TEXT_PRIMARY};
    }}
    QTableView::item:selected {{
        background: {ACCENT_LIGHT};
        color: {TEXT_PRIMARY};
    }}
    QHeaderView::section {{
        background: #F9F9F9;
        border: none;
        border-bottom: 1px solid {CARD_BORDER};
        border-right: 1px solid {CARD_BORDER};
        padding: 6px 10px;
        font-size: 11px;
        font-weight: 600;
        color: {TEXT_SECONDARY};
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    QHeaderView::section:first {{
        border-top-left-radius: 11px;
    }}
    QHeaderView::section:last {{
        border-top-right-radius: 11px;
        border-right: none;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
        border-radius: 3px;
    }}
    QScrollBar::handle:vertical {{
        background: #C7C7CC;
        border-radius: 3px;
        min-height: 20px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QLineEdit, QComboBox {{
        background: {CARD_BG};
        border: 1px solid {CARD_BORDER};
        border-radius: 8px;
        padding: 6px 10px;
        font-size: 12px;
        color: {TEXT_PRIMARY};
    }}
    QLineEdit:focus, QComboBox:focus {{
        border-color: {ACCENT};
    }}
    QLabel#page_title {{
        font-size: 28px;
        font-weight: 700;
        color: {TEXT_PRIMARY};
    }}
    QLabel#section_title {{
        font-size: 15px;
        font-weight: 600;
        color: {TEXT_PRIMARY};
    }}
    QLabel#metric_value {{
        font-size: 26px;
        font-weight: 700;
        color: {TEXT_PRIMARY};
    }}
    QLabel#metric_label {{
        font-size: 11px;
        font-weight: 500;
        color: {TEXT_SECONDARY};
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    QFrame#card {{
        background: {CARD_BG};
        border: 1px solid {CARD_BORDER};
        border-radius: 12px;
    }}
    QLabel {{
        color: {TEXT_PRIMARY};
    }}
    QGroupBox {{
        color: {TEXT_PRIMARY};
        font-size: 12px;
        font-weight: 600;
    }}
    QCheckBox {{
        color: {TEXT_PRIMARY};
        font-size: 12px;
    }}
    QRadioButton {{
        color: {TEXT_PRIMARY};
        font-size: 12px;
    }}
    QComboBox QAbstractItemView {{
        background: {CARD_BG};
        color: {TEXT_PRIMARY};
        border: 1px solid {CARD_BORDER};
        border-radius: 8px;
        selection-background-color: {ACCENT_LIGHT};
        selection-color: {TEXT_PRIMARY};
        outline: none;
    }}
    QMessageBox QLabel {{
        color: {TEXT_PRIMARY};
    }}
    QToolTip {{
        background: #1D1D1F;
        color: #FFFFFF;
        border: 1px solid #3A3A3C;
        padding: 5px 10px;
        border-radius: 6px;
        font-size: 12px;
    }}
    QSplitter::handle {{
        background: {CARD_BORDER};
    }}
    QLineEdit::placeholder-text {{
        color: {TEXT_MUTED};
    }}
    """
