from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QFrame, QSplitter, QButtonGroup, QPushButton
)

from core import analyzer
from core.store import AppStore
from ui.theme import ACCENT, CHART_COLORS, TEXT_SECONDARY
from ui.widgets.chart_canvas import ChartCanvas
from ui.widgets.sortable_table import SortableTable
from ui.widgets.metric_card import MetricCard


class CategoriesPage(QWidget):
    def __init__(self, store: AppStore, parent=None) -> None:
        super().__init__(parent)
        self._store = store
        self._cat_data = []
        self._chart_mode = "merchant"
        self._current_cat = ""
        self._build_ui()
        store.data_changed.connect(self.refresh)
        store.rules_changed.connect(self.refresh)

    def _build_ui(self) -> None:
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Left nav panel ────────────────────────────────────────────────────
        nav_panel = QWidget()
        nav_panel.setFixedWidth(220)
        nav_panel.setStyleSheet("background: #F5F5F5; border-right: 1px solid #EEEEEE;")
        nav_layout = QVBoxLayout(nav_panel)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)

        nav_header = QLabel("Categories")
        nav_header.setObjectName("page_title")
        nav_header.setStyleSheet(
            "font-size: 16px; font-weight: 700; color: #1D1D1F;"
            "padding: 20px 16px 12px 16px;"
        )
        nav_layout.addWidget(nav_header)

        self._cat_list = QListWidget()
        self._cat_list.setObjectName("nav")
        self._cat_list.setStyleSheet(
            "QListWidget { background: #F5F5F5; border: none; }"
            "QListWidget::item { color: #1D1D1F; padding: 10px 16px; border-radius: 8px; margin: 1px 8px; font-size: 12px; }"
            "QListWidget::item:selected { background: #E3F0FF; color: #0088CC; font-weight: 600; }"
            "QListWidget::item:hover:!selected { background: #E8E8ED; }"
        )
        self._cat_list.currentRowChanged.connect(self._on_category_selected)
        self._cat_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._cat_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        nav_layout.addWidget(self._cat_list)
        outer.addWidget(nav_panel)

        # ── Right content ─────────────────────────────────────────────────────
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 20, 24, 20)
        content_layout.setSpacing(16)

        # Title row
        self._detail_title = QLabel("Select a category")
        self._detail_title.setObjectName("section_title")
        self._detail_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #1D1D1F;")
        content_layout.addWidget(self._detail_title)

        # ── Top half: chart (left) + summary cards (right) ───────────────────
        top_row = QHBoxLayout()
        top_row.setSpacing(16)

        # Chart + toggle
        chart_frame = self._card_frame()
        chart_frame_layout = chart_frame.layout()

        # Toggle row
        toggle_row = QHBoxLayout()
        toggle_row.setSpacing(4)
        self._btn_merchant = QPushButton("By Merchant")
        self._btn_subcat = QPushButton("By Sub-category")
        for btn in (self._btn_merchant, self._btn_subcat):
            btn.setCheckable(True)
            btn.setFixedHeight(26)
            btn.setStyleSheet(
                "QPushButton { background: #EEEEEE; color: #1D1D1F; border: 1px solid #979797;"
                " border-radius: 4px; padding: 2px 10px; font-size: 11px; font-weight: 500; }"
                "QPushButton:checked { background: #0088CC; color: #FFFFFF; border-color: #0088CC; }"
            )
        self._btn_merchant.setChecked(True)
        self._btn_merchant.clicked.connect(lambda: self._set_chart_mode("merchant"))
        self._btn_subcat.clicked.connect(lambda: self._set_chart_mode("subcat"))
        toggle_row.addWidget(self._btn_merchant)
        toggle_row.addWidget(self._btn_subcat)
        toggle_row.addStretch()
        chart_frame_layout.addLayout(toggle_row)

        self._chart_mode = "merchant"
        self._sub_chart = ChartCanvas(figsize=(6, 2.8))
        chart_frame_layout.addWidget(self._sub_chart)
        top_row.addWidget(chart_frame, 3)

        # Summary cards (stacked vertically)
        summary_col = QVBoxLayout()
        summary_col.setSpacing(10)
        self._card_net = MetricCard("Net Spend")
        self._card_txcount = MetricCard("Transactions")
        self._card_merchants = MetricCard("Merchants")
        self._card_top = MetricCard("Largest Purchase")
        for c in [self._card_net, self._card_txcount, self._card_merchants, self._card_top]:
            summary_col.addWidget(c)
        summary_col.addStretch()
        top_row.addLayout(summary_col, 1)

        content_layout.addLayout(top_row)

        # ── Bottom half: full-width merchant table ────────────────────────────
        table_label = QLabel("Merchants in Category")
        table_label.setObjectName("section_title")
        content_layout.addWidget(table_label)

        self._tx_table = SortableTable(
            ["Merchant", "Sub-Category", "Net Spend", "# Transactions"]
        )
        self._tx_table.filter_changed.connect(self._update_cards_from_filter)
        content_layout.addWidget(self._tx_table, 1)

        outer.addWidget(content, 1)

    def _card_frame(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 8)
        return frame

    def refresh(self) -> None:
        df = self._store.df
        if df is None or df.empty:
            return

        self._cat_data = analyzer.category_totals(df).to_dict("records")
        self._cat_list.clear()
        for row in self._cat_data:
            label = f"{row['category']}  ${row['total_spend']:,.0f}"
            self._cat_list.addItem(label)

        if self._cat_list.count() > 0:
            self._cat_list.setCurrentRow(0)

    def _update_cards(self, subset) -> None:
        spend = subset[subset["amount"] > 0]
        net = subset["amount"].sum()
        merchants = subset["clean_merchant"].nunique()
        tx_count = len(subset)
        largest = spend["amount"].max() if not spend.empty else 0
        largest_m = spend.loc[spend["amount"].idxmax(), "clean_merchant"] if not spend.empty else "—"

        self._card_net.set_value(f"${net:,.0f}")
        self._card_txcount.set_value(str(tx_count))
        self._card_merchants.set_value(str(merchants))
        self._card_top.set_value(f"${largest:,.0f}")
        self._card_top.set_subtitle(largest_m[:24])

    def _update_cards_from_filter(self) -> None:
        if not hasattr(self, "_current_subset"):
            return
        visible_merchants = set(self._tx_table.visible_values(0))
        if not visible_merchants:
            self._update_cards(self._current_subset)
            return
        filtered = self._current_subset[self._current_subset["clean_merchant"].isin(visible_merchants)]
        self._update_cards(filtered)

    def _set_chart_mode(self, mode: str) -> None:
        self._chart_mode = mode
        self._btn_merchant.setChecked(mode == "merchant")
        self._btn_subcat.setChecked(mode == "subcat")
        self._redraw_chart()

    def _on_category_selected(self, row: int) -> None:
        if row < 0 or row >= len(self._cat_data):
            return
        df = self._store.df
        if df is None:
            return

        cat = self._cat_data[row]["category"]
        total = self._cat_data[row]["total_spend"]
        self._detail_title.setText(f"{cat}  —  ${total:,.0f} net")

        self._current_subset = df[df["category"] == cat]
        self._current_cat = cat

        self._update_cards(self._current_subset)
        self._redraw_chart()

        # Merchant table
        RIGHT = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
        CENTER = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter

        grouped = (
            self._current_subset.groupby("clean_merchant")
            .agg(
                net_spend=("amount", "sum"),
                tx_count=("amount", "count"),
                sub_category=("sub_category", lambda x: x[x != ""].iloc[0] if (x != "").any() else "—"),
            )
            .reset_index()
            .sort_values("net_spend", ascending=False)
        )

        rows = []
        row_colors = []
        for _, r in grouped.iterrows():
            is_net_refund = r["net_spend"] <= 0
            amount_str = f"-${abs(r['net_spend']):,.2f}" if is_net_refund else f"${r['net_spend']:,.2f}"
            rows.append([r["clean_merchant"], r["sub_category"], amount_str, str(int(r["tx_count"]))])
            row_colors.append("#22C55E" if is_net_refund else None)

        self._tx_table.populate(rows, [
            Qt.AlignmentFlag.AlignVCenter,
            Qt.AlignmentFlag.AlignVCenter,
            RIGHT,
            CENTER,
        ], row_colors=row_colors)

    def _redraw_chart(self) -> None:
        if not hasattr(self, "_current_subset"):
            return

        subset = self._current_subset
        cat = self._current_cat
        df = self._store.df

        if self._chart_mode == "merchant":
            top = (
                subset.groupby("clean_merchant")["amount"]
                .sum()
                .sort_values(ascending=False)
                .head(8)
            )

            def draw_merchant(fig):
                ax = fig.add_subplot(111)
                if not top.empty:
                    ax.barh(top.index, top.values, color=ACCENT, alpha=0.85)
                    ax.invert_yaxis()
                    ax.set_title("Top Merchants by Net Spend", fontsize=11)
                    ax.set_xlabel("Net Spend ($)", fontsize=10, color="#666666", labelpad=6)
                    ax.xaxis.set_major_formatter(lambda x, _: f"${x:,.0f}")
                    ax.spines[["top", "right", "bottom"]].set_visible(False)
                    ax.spines["left"].set_color("#979797")
                else:
                    ax.text(0.5, 0.5, "No data", ha="center", va="center",
                            transform=ax.transAxes, color="#979797")
                    ax.axis("off")
                fig.patch.set_facecolor("#FFFFFF")
                ax.set_facecolor("#FFFFFF")

            self._sub_chart.update_figure(draw_merchant)

        else:
            sub_totals = analyzer.sub_category_totals(df)
            sub_for_cat = sub_totals[sub_totals["category"] == cat]

            def draw_subcat(fig):
                ax = fig.add_subplot(111)
                if not sub_for_cat.empty:
                    vals = sub_for_cat["total_spend"].values
                    labels = sub_for_cat["sub_category"].values
                    _, _, autotexts = ax.pie(
                        vals, labels=labels, autopct="%1.1f%%",
                        colors=CHART_COLORS[:len(vals)],
                        startangle=90, pctdistance=0.8,
                        wedgeprops={"linewidth": 1, "edgecolor": "white"}
                    )
                    for t in autotexts:
                        t.set_fontsize(9)
                    ax.set_title("Sub-categories", fontsize=11, pad=10)
                else:
                    ax.text(0.5, 0.5, "No tags set yet\nAdd rules on the Tagging Rules page",
                            ha="center", va="center", transform=ax.transAxes,
                            color="#979797", fontsize=10)
                    ax.axis("off")
                fig.patch.set_facecolor("#FFFFFF")
                ax.set_facecolor("#FFFFFF")

            self._sub_chart.update_figure(draw_subcat)
