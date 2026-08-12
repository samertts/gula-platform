from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config import AppConfig
from l10n import TranslationManager
from session import SessionManager
from widgets.charts import OccupancyGauge, SearchBar
from widgets.dialogs import AlertDialog


class ResourceView(QWidget):
    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self._config = config
        self._tr = TranslationManager(config.language)
        self._session = SessionManager()
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel(self._tr.get("resources"))
        title.setProperty("heading", True)
        header.addWidget(title)
        header.addStretch()
        main_layout.addLayout(header)

        overview_layout = QHBoxLayout()
        overview_layout.setSpacing(16)

        gauge = OccupancyGauge()
        gauge.set_value(78.5, "\u0625\u0634\u063a\u0627\u0644 \u0627\u0644\u0623\u0633\u0631\u0629")
        overview_layout.addWidget(gauge)

        stats_defs = [
            ("\u0625\u062c\u0645\u0627\u0644\u064a \u0627\u0644\u0623\u0633\u0631\u0629", "138", "#58a6ff"),
            ("\u0623\u0633\u0631\u0629 \u0645\u0634\u063a\u0648\u0644\u0629", "108", "#d29922"),
            ("\u0623\u0633\u0631\u0629 \u0645\u062a\u0627\u062d\u0629", "30", "#3fb950"),
            ("\u0642\u064a\u062f \u0627\u0644\u0635\u064a\u0627\u0646\u0629", "8", "#6e7681"),
        ]
        for label, val, color in stats_defs:
            g = QGroupBox()
            g.setStyleSheet(f"QGroupBox {{ border: 1px solid {color}; border-radius: 8px; padding: 12px; }}")
            gl = QVBoxLayout(g)
            v = QLabel(val)
            v.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {color};")
            v.setAlignment(Qt.AlignmentFlag.AlignCenter)
            gl.addWidget(v)
            l = QLabel(label)
            l.setStyleSheet("color: #8b949e; font-size: 11px;")
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            gl.addWidget(l)
            overview_layout.addWidget(g, 1)

        main_layout.addLayout(overview_layout)

        self._tabs = QTabWidget()

        beds_tab = QWidget()
        beds_layout = QVBoxLayout(beds_tab)
        beds_layout.setContentsMargins(12, 12, 12, 12)

        beds_filter = QHBoxLayout()
        beds_filter.addWidget(QLabel(self._tr.get("department") + ":"))
        self._dept_filter = QComboBox()
        self._dept_filter.addItems(["\u062c\u0645\u064a\u0639 \u0627\u0644\u0623\u0642\u0633\u0627\u0645",
                                     "\u0627\u0644\u0637\u0648\u0627\u0631\u0626", "\u0627\u0644\u0639\u0646\u0627\u064a\u0629 \u0627\u0644\u0645\u0631\u0643\u0632\u0629",
                                     "\u0627\u0644\u062c\u0631\u0627\u062d\u0629", "\u0637\u0628 \u0627\u0644\u0623\u0637\u0641\u0627\u0644"])
        beds_filter.addWidget(self._dept_filter)
        beds_filter.addStretch()
        beds_layout.addLayout(beds_filter)

        self._beds_table = QTableWidget()
        self._beds_table.setColumnCount(6)
        self._beds_table.setHorizontalHeaderLabels([
            "\u0627\u0644\u0642\u0633\u0645", "\u0631\u0642\u0645 \u0627\u0644\u063a\u0631\u0641\u0629",
            "\u0631\u0642\u0645 \u0627\u0644\u0633\u0631\u064a\u0631", "\u0627\u0644\u0645\u0631\u064a\u0636", "\u0627\u0644\u062d\u0627\u0644\u0629", "\u0645\u0644\u0627\u062d\u0638\u0627\u062a"
        ])
        self._beds_table.horizontalHeader().setStretchLastSection(True)

        beds_data = [
            ["\u0627\u0644\u0637\u0648\u0627\u0631\u0626", "A-101", "01", "\u0623\u062d\u0645\u062f \u0639\u0644\u064a", "\u0645\u0634\u063a\u0648\u0644", ""],
            ["\u0627\u0644\u0637\u0648\u0627\u0631\u0626", "A-101", "02", "", "\u0645\u062a\u0627\u062d", "\u062a\u0645 \u0627\u0644\u062a\u0646\u0638\u064a\u0641"],
            ["\u0627\u0644\u0639\u0646\u0627\u064a\u0629 \u0627\u0644\u0645\u0631\u0643\u0632\u0629", "ICU-01", "01", "\u0633\u0627\u0631\u0629 \u0639\u0628\u062f \u0627\u0644\u0644\u0647", "\u0645\u0634\u063a\u0648\u0644", "\u062c\u0647\u0627\u0632 \u062a\u0646\u0641\u0633"],
            ["\u0627\u0644\u062c\u0631\u0627\u062d\u0629", "C-301", "12", "\u064a\u0648\u0633\u0641 \u0645\u062d\u0645\u062f", "\u0645\u0634\u063a\u0648\u0644", ""],
            ["\u0637\u0628 \u0627\u0644\u0623\u0637\u0641\u0627\u0644", "B-202", "08", "\u0639\u0644\u064a \u062d\u0633\u0646", "\u0645\u0634\u063a\u0648\u0644", ""],
            ["\u0627\u0644\u0642\u0644\u0628", "B-201", "05", "\u0645\u0631\u064a\u0645 \u062e\u0627\u0644\u062f", "\u0645\u0634\u063a\u0648\u0644", ""],
            ["\u0627\u0644\u062c\u0631\u0627\u062d\u0629", "C-302", "15", "", "\u0635\u064a\u0627\u0646\u0629", "\u062a\u0646\u0638\u064a\u0641 \u0639\u0627\u0645"],
        ]
        self._beds_table.setRowCount(len(beds_data))
        for i, row in enumerate(beds_data):
            for j, val in enumerate(row):
                item = QTableWidgetItem(val)
                status = row[4]
                if status == "\u0645\u062a\u0627\u062d":
                    item.setForeground(QColor("#3fb950"))
                elif status == "\u0635\u064a\u0627\u0646\u0629":
                    item.setForeground(QColor("#d29922"))
                self._beds_table.setItem(i, j, item)

        beds_layout.addWidget(self._beds_table)

        self._tabs.addTab(beds_tab, self._tr.get("beds"))

        rooms_tab = QWidget()
        rooms_layout = QVBoxLayout(rooms_tab)
        rooms_layout.setContentsMargins(12, 12, 12, 12)

        self._rooms_table = QTableWidget()
        self._rooms_table.setColumnCount(5)
        self._rooms_table.setHorizontalHeaderLabels([
            "\u0627\u0644\u0642\u0633\u0645", "\u0631\u0642\u0645 \u0627\u0644\u063a\u0631\u0641\u0629",
            "\u0639\u062f\u062f \u0627\u0644\u0623\u0633\u0631\u0629", "\u0627\u0644\u062d\u0627\u0644\u0629", "\u0622\u062e\u0631 \u062a\u0646\u0638\u064a\u0641"
        ])
        self._rooms_table.horizontalHeader().setStretchLastSection(True)

        rooms_data = [
            ["\u0627\u0644\u0637\u0648\u0627\u0631\u0626", "A-101", "2", "\u0646\u0634\u0637", "15/07/2026"],
            ["\u0627\u0644\u0637\u0648\u0627\u0631\u0626", "A-102", "2", "\u062a\u0646\u0638\u064a\u0641", "14/07/2026"],
            ["\u0627\u0644\u0639\u0646\u0627\u064a\u0629 \u0627\u0644\u0645\u0631\u0643\u0632\u0629", "ICU-01", "1", "\u0646\u0634\u0637", "15/07/2026"],
            ["\u0627\u0644\u062c\u0631\u0627\u062d\u0629", "C-301", "4", "\u0646\u0634\u0637", "15/07/2026"],
            ["\u0627\u0644\u062c\u0631\u0627\u062d\u0629", "C-302", "4", "\u062a\u0646\u0638\u064a\u0641", "12/07/2026"],
        ]
        self._rooms_table.setRowCount(len(rooms_data))
        for i, row in enumerate(rooms_data):
            for j, val in enumerate(row):
                self._rooms_table.setItem(i, j, QTableWidgetItem(val))

        rooms_layout.addWidget(self._rooms_table)
        self._tabs.addTab(rooms_tab, self._tr.get("rooms"))

        equip_tab = QWidget()
        equip_layout = QVBoxLayout(equip_tab)
        equip_layout.setContentsMargins(12, 12, 12, 12)

        self._equip_table = QTableWidget()
        self._equip_table.setColumnCount(6)
        self._equip_table.setHorizontalHeaderLabels([
            "\u0627\u0644\u0645\u0639\u062f\u0627\u062a", "\u0627\u0644\u0642\u0633\u0645", "\u0627\u0644\u0637\u0631\u0627\u0632",
            "\u062d\u0627\u0644\u0629 \u0627\u0644\u062a\u0634\u063a\u064a\u0644", "\u0622\u062e\u0631 \u0635\u064a\u0627\u0646\u0629", "\u0627\u0644\u0645\u0648\u0639\u062f \u0627\u0644\u062a\u0627\u0644\u064a"
        ])
        self._equip_table.horizontalHeader().setStretchLastSection(True)

        equip_data = [
            ["\u062c\u0647\u0627\u0632 \u062a\u0646\u0641\u0633", "\u0627\u0644\u0639\u0646\u0627\u064a\u0629 \u0627\u0644\u0645\u0631\u0643\u0632\u0629", "Drager", "\u0639\u0627\u0645\u0644", "01/07/2026", "01/08/2026"],
            ["\u0645\u0648\u0646\u064a\u062a\u0648\u0631 \u0642\u0644\u0628", "\u0627\u0644\u0637\u0648\u0627\u0631\u0626", "Philips", "\u0639\u0627\u0645\u0644", "15/06/2026", "15/09/2026"],
            ["\u062c\u0647\u0627\u0632 \u0623\u0634\u0639\u0629", "\u0627\u0644\u0623\u0634\u0639\u0629", "Siemens", "\u0642\u064a\u062f \u0627\u0644\u0635\u064a\u0627\u0646\u0629", "10/07/2026", "25/07/2026"],
            ["\u0645\u062e\u0628\u0631 \u062f\u0645", "\u0627\u0644\u0645\u062e\u062a\u0628\u0631", "Sysmex", "\u0639\u0627\u0645\u0644", "01/07/2026", "01\/10\/2026"],
            ["\u062c\u0647\u0627\u0632 \u062a\u062e\u062f\u064a\u0631", "\u0627\u0644\u062c\u0631\u0627\u062d\u0629", "GE", "\u0639\u0627\u0637\u0644", "05/06/2026", "05/08/2026"],
        ]
        self._equip_table.setRowCount(len(equip_data))
        for i, row in enumerate(equip_data):
            for j, val in enumerate(row):
                item = QTableWidgetItem(val)
                status = row[3]
                if status == "\u0639\u0627\u0637\u0644":
                    item.setForeground(QColor("#f85149"))
                elif status == "\u0642\u064a\u062f \u0627\u0644\u0635\u064a\u0627\u0646\u0629":
                    item.setForeground(QColor("#d29922"))
                self._equip_table.setItem(i, j, item)

        equip_layout.addWidget(self._equip_table)
        self._tabs.addTab(equip_tab, self._tr.get("equipment"))

        main_layout.addWidget(self._tabs)
