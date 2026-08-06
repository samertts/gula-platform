from __future__ import annotations

from datetime import datetime, timedelta

from l10n import TranslationManager
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from session import SessionManager
from widgets.charts import KpiCard, OccupancyGauge, TrendChart

from config import AppConfig

DEPT_COLORS = {
    "\u0627\u0644\u0637\u0648\u0627\u0631\u0626": "#f85149",
    "\u0627\u0644\u0639\u0646\u0627\u064a\u0629 \u0627\u0644\u0645\u0631\u0643\u0632\u0629": "#d29922",
    "\u0627\u0644\u062c\u0631\u0627\u062d\u0629": "#58a6ff",
    "\u0637\u0628 \u0627\u0644\u0623\u0637\u0641\u0627\u0644": "#3fb950",
    "\u0627\u0644\u0642\u0644\u0628": "#f0883e",
    "\u0627\u0644\u0639\u0638\u0627\u0645": "#bc8cff",
    "\u0627\u0644\u0646\u0633\u0627\u0621": "#ff7b72",
}


class DashboardView(QWidget):
    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self._config = config
        self._tr = TranslationManager(config.language)
        self._session = SessionManager()
        self._auto_refresh_timer = QTimer(self)
        self._auto_refresh_timer.timeout.connect(self.refresh_data)

        self.setup_ui()
        self.refresh_data()

        if self._config.auto_refresh_interval > 0:
            self._auto_refresh_timer.start(self._config.auto_refresh_interval * 1000)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel(self._tr.get("dashboard"))
        title.setProperty("heading", True)
        header.addWidget(title)

        header.addStretch()

        self._date_range = QComboBox()
        self._date_range.addItems([
            self._tr.get("today"),
            self._tr.get("this_week"),
            self._tr.get("this_month"),
            self._tr.get("custom_range"),
        ])
        self._date_range.setMinimumWidth(140)
        header.addWidget(self._date_range)

        self._refresh_btn = QPushButton("\u21bb " + self._tr.get("refresh"))
        self._refresh_btn.setProperty("secondary", True)
        self._refresh_btn.clicked.connect(self.refresh_data)
        header.addWidget(self._refresh_btn)

        main_layout.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(12)

        kpi_defs = [
            ("\U0001f3e5", "\u0627\u0644\u0627\u0633\u062a\u0642\u0628\u0627\u0644\u0627\u062a \u0627\u0644\u064a\u0648\u0645", "---", "\u25b2 12%", "#58a6ff"),
            ("\U0001f6aa", "\u0627\u0644\u062e\u0631\u0648\u062c \u0627\u0644\u064a\u0648\u0645", "---", "\u25bc 5%", "#3fb950"),
            ("\U0001f504", "\u0627\u0644\u062a\u062d\u0648\u064a\u0644\u0627\u062a \u0627\u0644\u064a\u0648\u0645", "---", "", "#f0883e"),
            ("\U0001f3e8", "\u0646\u0633\u0628\u0629 \u0627\u0644\u0625\u0634\u063a\u0627\u0644", "---", "", "#d29922"),
            ("\u23f0", "\u0645\u062a\u0648\u0633\u0637 \u0627\u0644\u0625\u0642\u0627\u0645\u0629", "---", "", "#bc8cff"),
            ("\u26a0\ufe0f", "\u0627\u0646\u062a\u0638\u0627\u0631 \u0627\u0644\u0637\u0648\u0627\u0631\u0626", "---", "\u25b2 8%", "#f85149"),
        ]

        for i, (icon, label, value, trend, color) in enumerate(kpi_defs):
            card = KpiCard(icon, label, value, trend, color)
            kpi_grid.addWidget(card, i // 3, i % 3)
            self._kpi_cards[label] = card

        content_layout.addLayout(kpi_grid)

        charts_row = QHBoxLayout()
        charts_row.setSpacing(16)

        gauge_group = QGroupBox(self._tr.get("bed_occupancy"))
        gauge_layout = QVBoxLayout(gauge_group)
        self._occupancy_gauge = OccupancyGauge()
        gauge_layout.addWidget(self._occupancy_gauge)
        charts_row.addWidget(gauge_group)

        trend_group = QGroupBox(self._tr.get("kpi_admissions_today") + " / " + self._tr.get("kpi_discharges_today"))
        trend_layout = QVBoxLayout(trend_group)
        self._trend_chart = TrendChart()
        trend_layout.addWidget(self._trend_chart)
        charts_row.addWidget(trend_group)

        content_layout.addLayout(charts_row)

        dept_group = QGroupBox(self._tr.get("departments"))
        dept_layout = QVBoxLayout(dept_group)
        self._dept_table = QTableWidget()
        self._dept_table.setColumnCount(5)
        self._dept_table.setHorizontalHeaderLabels([
            self._tr.get("department"),
            self._tr.get("total_beds"),
            "\u0645\u0634\u063a\u0648\u0644",
            self._tr.get("available_beds"),
            self._tr.get("occupancy_rate"),
        ])
        self._dept_table.horizontalHeader().setStretchLastSection(True)
        self._dept_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._dept_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        dept_layout.addWidget(self._dept_table)
        content_layout.addWidget(dept_group)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)

        alerts_group = QGroupBox("\u0627\u0644\u062a\u0646\u0628\u064a\u0647\u0627\u062a \u0627\u0644\u062d\u0631\u062c\u0629")
        alerts_layout = QVBoxLayout(alerts_group)
        self._alerts_table = QTableWidget()
        self._alerts_table.setColumnCount(4)
        self._alerts_table.setHorizontalHeaderLabels(["\u0627\u0644\u0646\u0648\u0639", "\u0627\u0644\u0645\u0631\u064a\u0636", "\u0627\u0644\u062d\u0627\u0644\u0629", "\u0627\u0644\u0648\u0642\u062a"])
        self._alerts_table.horizontalHeader().setStretchLastSection(True)
        self._alerts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._alerts_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        alerts_layout.addWidget(self._alerts_table)
        bottom_row.addWidget(alerts_group)

        icu_group = QGroupBox("\u0627\u0644\u0639\u0646\u0627\u064a\u0629 \u0627\u0644\u0645\u0631\u0643\u0632\u0629 / \u063a\u0631\u0641 \u0627\u0644\u0639\u0645\u0644\u064a\u0627\u062a")
        icu_layout = QVBoxLayout(icu_group)
        self._icu_gauge = OccupancyGauge()
        icu_layout.addWidget(self._icu_gauge)
        icu_label = QLabel("\u0625\u0634\u063a\u0627\u0644 \u0627\u0644\u0639\u0646\u0627\u064a\u0629 \u0627\u0644\u0645\u0631\u0643\u0632\u0629")
        icu_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icu_layout.addWidget(icu_label)

        self._or_gauge = OccupancyGauge()
        icu_layout.addWidget(self._or_gauge)
        or_label = QLabel("\u0625\u0634\u063a\u0627\u0644 \u063a\u0631\u0641 \u0627\u0644\u0639\u0645\u0644\u064a\u0627\u062a")
        or_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icu_layout.addWidget(or_label)

        bottom_row.addWidget(icu_group)
        content_layout.addLayout(bottom_row)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def refresh_data(self):
        self._load_kpi_data()
        self._load_chart_data()
        self._load_department_data()
        self._load_alert_data()
        self._load_icu_data()

    def _load_kpi_data(self):
        kpis = {
            "\u0627\u0644\u0627\u0633\u062a\u0642\u0628\u0627\u0644\u0627\u062a \u0627\u0644\u064a\u0648\u0645": ("24", "\u25b2 12%"),
            "\u0627\u0644\u062e\u0631\u0648\u062c \u0627\u0644\u064a\u0648\u0645": ("18", "\u25b2 5%"),
            "\u0627\u0644\u062a\u062d\u0648\u064a\u0644\u0627\u062a \u0627\u0644\u064a\u0648\u0645": ("3", ""),
            "\u0646\u0633\u0628\u0629 \u0627\u0644\u0625\u0634\u063a\u0627\u0644": "78%",
            "\u0645\u062a\u0648\u0633\u0637 \u0627\u0644\u0625\u0642\u0627\u0645\u0629": "4.2 \u0623\u064a\u0627\u0645",
            "\u0627\u0646\u062a\u0638\u0627\u0631 \u0627\u0644\u0637\u0648\u0627\u0631\u0626": "12 \u062f\u0642\u064a\u0642\u0629",
        }

    def _load_chart_data(self):
        days = [(datetime.now() - timedelta(days=i)).strftime("%a") for i in range(6, -1, -1)]
        admissions = [12, 15, 8, 20, 18, 14, 24]
        discharges = [10, 13, 6, 17, 15, 11, 18]
        data_adm = list(zip(days, admissions))
        data_dis = list(zip(days, discharges))
        self._trend_chart.add_series("\u0627\u0644\u0627\u0633\u062a\u0642\u0628\u0627\u0644\u0627\u062a", data_adm, "#58a6ff")
        self._trend_chart.add_series("\u0627\u0644\u062e\u0631\u0648\u062c", data_dis, "#3fb950")

    def _load_department_data(self):
        depts = [
            ("\u0627\u0644\u0637\u0648\u0627\u0631\u0626", 20, 18, 2, "90%"),
            ("\u0627\u0644\u0639\u0646\u0627\u064a\u0629 \u0627\u0644\u0645\u0631\u0643\u0632\u0629", 10, 9, 1, "90%"),
            ("\u0627\u0644\u062c\u0631\u0627\u062d\u0629", 30, 22, 8, "73%"),
            ("\u0637\u0628 \u0627\u0644\u0623\u0637\u0641\u0627\u0644", 25, 18, 7, "72%"),
            ("\u0627\u0644\u0642\u0644\u0628", 15, 12, 3, "80%"),
            ("\u0627\u0644\u0639\u0638\u0627\u0645", 20, 14, 6, "70%"),
            ("\u0627\u0644\u0646\u0633\u0627\u0621 \u0648\u0627\u0644\u062a\u0648\u0644\u064a\u062f", 18, 15, 3, "83%"),
        ]
        self._dept_table.setRowCount(len(depts))
        for i, (name, total, occ, avail, rate) in enumerate(depts):
            self._dept_table.setItem(i, 0, QTableWidgetItem(name))
            self._dept_table.setItem(i, 1, QTableWidgetItem(str(total)))
            self._dept_table.setItem(i, 2, QTableWidgetItem(str(occ)))
            self._dept_table.setItem(i, 3, QTableWidgetItem(str(avail)))
            item = QTableWidgetItem(rate)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._dept_table.setItem(i, 4, item)

        self._occupancy_gauge.set_value(78.5, "\u0625\u062c\u0645\u0627\u0644\u064a \u0627\u0644\u0645\u0633\u062a\u0634\u0641\u0649")

    def _load_alert_data(self):
        alerts = [
            ("\U0001f525 \u062d\u0627\u0644\u0629 \u062d\u0631\u062c\u0629", "\u0645\u0631\u064a\u0636 0042", "\u0646\u0634\u0637", "\u0645\u0646\u0630 5 \u062f\u0642\u0627\u0626\u0642"),
            ("\u26a0\ufe0f \u062a\u0646\u0628\u064a\u0647 \u062f\u0648\u0627\u0626\u064a", "\u0645\u0631\u064a\u0636 0087", "\u062c\u062f\u064a\u062f", "\u0645\u0646\u0630 15 \u062f\u0642\u064a\u0642\u0629"),
            ("\U0001f3e5 \u062a\u062d\u0648\u064a\u0644 \u0637\u0627\u0631\u0626", "\u0645\u0631\u064a\u0636 0031", "\u0642\u064a\u062f \u0627\u0644\u0645\u0639\u0627\u0644\u062c\u0629", "\u0645\u0646\u0630 30 \u062f\u0642\u064a\u0642\u0629"),
        ]
        self._alerts_table.setRowCount(len(alerts))
        for i, (typ, pt, status, time_str) in enumerate(alerts):
            self._alerts_table.setItem(i, 0, QTableWidgetItem(typ))
            self._alerts_table.setItem(i, 1, QTableWidgetItem(pt))
            self._alerts_table.setItem(i, 2, QTableWidgetItem(status))
            self._alerts_table.setItem(i, 3, QTableWidgetItem(time_str))

    def _load_icu_data(self):
        self._icu_gauge.set_value(90.0, "\u0627\u0644\u0639\u0646\u0627\u064a\u0629 \u0627\u0644\u0645\u0631\u0643\u0632\u0629")
        self._or_gauge.set_value(65.0, "\u063a\u0631\u0641 \u0627\u0644\u0639\u0645\u0644\u064a\u0627\u062a")


DashboardView._kpi_cards = {}
