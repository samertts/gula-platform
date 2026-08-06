from __future__ import annotations

from l10n import TranslationManager
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from session import SessionManager
from widgets.charts import KpiCard, MiniChart
from widgets.dialogs import DateRangeDialog

from config import AppConfig


class ReportsView(QWidget):
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
        title = QLabel(self._tr.get("reports"))
        title.setProperty("heading", True)
        header.addWidget(title)
        header.addStretch()

        self._date_btn = QPushButton("\u2b50 " + self._tr.get("custom_range"))
        self._date_btn.setProperty("secondary", True)
        self._date_btn.clicked.connect(self._show_date_range)
        header.addWidget(self._date_btn)

        export_pdf_btn = QPushButton(self._tr.get("export_pdf"))
        export_pdf_btn.setProperty("secondary", True)
        header.addWidget(export_pdf_btn)

        export_xls_btn = QPushButton(self._tr.get("export_excel"))
        export_xls_btn.setProperty("secondary", True)
        header.addWidget(export_xls_btn)

        print_btn = QPushButton(self._tr.get("print"))
        print_btn.setProperty("secondary", True)
        header.addWidget(print_btn)

        main_layout.addLayout(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 8, 0)

        templates_label = QLabel("\u0642\u0648\u0627\u0644\u0628 \u0627\u0644\u062a\u0642\u0627\u0631\u064a\u0631")
        templates_label.setProperty("subheading", True)
        left_layout.addWidget(templates_label)

        self._template_list = QListWidget()
        templates = [
            "\u0645\u0644\u062e\u0635 \u0627\u0644\u0627\u0633\u062a\u0642\u0628\u0627\u0644\u0627\u062a",
            "\u0645\u0644\u062e\u0635 \u0627\u0644\u062e\u0631\u0648\u062c",
            "\u062a\u0639\u062f\u0627\u062f \u0627\u0644\u0645\u0631\u0636\u0649",
            "\u0633\u062c\u0644 \u0627\u0644\u0639\u0645\u0644\u064a\u0627\u062a",
            "\u062a\u0642\u0631\u064a\u0631 \u0627\u0644\u0625\u0634\u063a\u0627\u0644",
            "\u062a\u0642\u0631\u064a\u0631 \u0627\u0644\u0637\u0648\u0627\u0631\u0626",
            "\u0625\u062d\u0635\u0627\u0621\u064a\u0627\u062a \u0627\u0644\u0645\u0633\u062a\u0634\u0641\u0649",
            "\u062a\u0642\u0631\u064a\u0631 \u0645\u0643\u0627\u0641\u062d\u0629 \u0627\u0644\u0639\u062f\u0648\u0649",
        ]
        for t in templates:
            item = QListWidgetItem(t)
            item.setSizeHint(Qt.QSize(0, 36))
            self._template_list.addItem(item)

        self._template_list.currentRowChanged.connect(self._on_template_selected)
        left_layout.addWidget(self._template_list)

        splitter.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(8, 0, 0, 0)

        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)
        kpi_defs = [
            ("\u0625\u062c\u0645\u0627\u0644\u064a \u0627\u0644\u0645\u0631\u0636\u0649", "187", "\u25b2 8%", "#58a6ff"),
            ("\u0645\u062a\u0648\u0633\u0637 \u0627\u0644\u0625\u0642\u0627\u0645\u0629", "4.2 \u0623\u064a\u0627\u0645", "\u25bc 0.5", "#3fb950"),
            ("\u0645\u0639\u062f\u0644 \u0625\u0634\u063a\u0627\u0644 \u0627\u0644\u0623\u0633\u0631\u0629", "78.5%", "", "#d29922"),
        ]
        for label, value, trend, color in kpi_defs:
            card = KpiCard("", label, value, trend, color)
            kpi_row.addWidget(card)

        right_layout.addLayout(kpi_row)

        chart_row = QHBoxLayout()
        chart_row.setSpacing(16)

        adm_trend = QGroupBox("\u0627\u062a\u062c\u0627\u0647 \u0627\u0644\u0627\u0633\u062a\u0642\u0628\u0627\u0644\u0627\u062a")
        chart_l = QVBoxLayout(adm_trend)
        self._adm_chart = MiniChart()
        self._adm_chart.set_data([20, 25, 18, 30, 22, 28, 24])
        chart_l.addWidget(self._adm_chart)
        chart_row.addWidget(adm_trend)

        los_chart = QGroupBox("\u0645\u062a\u0648\u0633\u0637 \u0645\u062f\u0629 \u0627\u0644\u0625\u0642\u0627\u0645\u0629")
        chart_l2 = QVBoxLayout(los_chart)
        self._los_chart = MiniChart()
        self._los_chart.set_data([3.5, 4.0, 3.8, 4.2, 4.5, 4.1, 4.2])
        chart_l2.addWidget(self._los_chart)
        chart_row.addWidget(los_chart)

        right_layout.addLayout(chart_row)

        self._report_table = QTableWidget()
        self._report_table.setColumnCount(6)
        self._report_table.setHorizontalHeaderLabels([
            "\u0627\u0644\u0642\u0633\u0645", "\u0627\u0644\u0627\u0633\u062a\u0642\u0628\u0627\u0644\u0627\u062a",
            "\u0627\u0644\u062e\u0631\u0648\u062c", "\u0627\u0644\u0623\u0633\u0631\u0629 \u0627\u0644\u0645\u0634\u063a\u0648\u0644\u0629",
            "\u0625\u062c\u0645\u0627\u0644\u064a \u0627\u0644\u0623\u0633\u0631\u0629", "\u0646\u0633\u0628\u0629 \u0627\u0644\u0625\u0634\u063a\u0627\u0644"
        ])
        self._report_table.horizontalHeader().setStretchLastSection(True)

        report_data = [
            ["\u0627\u0644\u0637\u0648\u0627\u0631\u0626", "45", "38", "18", "20", "90%"],
            ["\u0627\u0644\u0639\u0646\u0627\u064a\u0629 \u0627\u0644\u0645\u0631\u0643\u0632\u0629", "12", "10", "9", "10", "90%"],
            ["\u0627\u0644\u062c\u0631\u0627\u062d\u0629", "35", "30", "22", "30", "73%"],
            ["\u0637\u0628 \u0627\u0644\u0623\u0637\u0641\u0627\u0644", "28", "25", "18", "25", "72%"],
            ["\u0627\u0644\u0642\u0644\u0628", "20", "18", "12", "15", "80%"],
            ["\u0627\u0644\u0639\u0638\u0627\u0645", "25", "20", "14", "20", "70%"],
            ["\u0627\u0644\u0646\u0633\u0627\u0621", "22", "18", "15", "18", "83%"],
        ]
        self._report_table.setRowCount(len(report_data))
        for i, row in enumerate(report_data):
            for j, val in enumerate(row):
                item = QTableWidgetItem(val)
                if j == 5:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._report_table.setItem(i, j, item)

        right_layout.addWidget(self._report_table)

        splitter.addWidget(right_panel)
        splitter.setSizes([220, 600])

        main_layout.addWidget(splitter)

    def _show_date_range(self):
        dialog = DateRangeDialog(self)
        dialog.range_selected.connect(lambda s, e: self._date_btn.setText(f"{s} - {e}"))
        dialog.exec()

    def _on_template_selected(self, index: int):
        pass
