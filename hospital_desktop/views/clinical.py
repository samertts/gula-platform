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
    QLineEdit,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from config import AppConfig
from l10n import TranslationManager
from session import SessionManager
from widgets.charts import MiniChart, SearchBar
from widgets.dialogs import AlertDialog, ConfirmDialog


class WardRoundForm(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("\u062c\u0648\u0644\u0629 \u0633\u0631\u064a\u0631\u064a\u0629 \u062c\u062f\u064a\u062f\u0629")
        title.setProperty("heading", True)
        layout.addWidget(title)

        form = QFormLayout()
        self._patient_input = QLineEdit()
        self._patient_input.setPlaceholderText("\u0627\u0633\u0645 / \u0631\u0642\u0645 \u0627\u0644\u0645\u0631\u064a\u0636")
        form.addRow("\u0627\u0644\u0645\u0631\u064a\u0636:", self._patient_input)

        self._doctor_input = QLineEdit()
        self._doctor_input.setPlaceholderText("\u0627\u0633\u0645 \u0627\u0644\u0637\u0628\u064a\u0628")
        form.addRow("\u0627\u0644\u0637\u0628\u064a\u0628:", self._doctor_input)

        self._findings = QTextEdit()
        self._findings.setPlaceholderText("\u0627\u0644\u0645\u0644\u0627\u062d\u0638\u0627\u062a \u0627\u0644\u0633\u0631\u064a\u0631\u064a\u0629...")
        self._findings.setMaximumHeight(120)
        form.addRow("\u0627\u0644\u0645\u0644\u0627\u062d\u0638\u0627\u062a:", self._findings)

        layout.addLayout(form)

        btn = QPushButton("\u062d\u0641\u0638 \u0627\u0644\u062c\u0648\u0644\u0629")
        btn.setMinimumHeight(36)
        btn.clicked.connect(lambda: AlertDialog(
            "\u062a\u0645 \u0627\u0644\u062d\u0641\u0638", "\u062a\u0645 \u062a\u0633\u062c\u064a\u0644 \u0627\u0644\u062c\u0648\u0644\u0629 \u0627\u0644\u0633\u0631\u064a\u0631\u064a\u0629 \u0628\u0646\u062c\u0627\u062d", "success", parent=self
        ).exec())
        layout.addWidget(btn)


class ClinicalView(QWidget):
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
        title = QLabel(self._tr.get("clinical_tasks"))
        title.setProperty("heading", True)
        header.addWidget(title)
        header.addStretch()

        self._search = SearchBar(self._tr.get("search") + "...")
        header.addWidget(self._search)

        new_round_btn = QPushButton("+ " + self._tr.get("ward_rounds"))
        new_round_btn.clicked.connect(self._toggle_round_form)
        header.addWidget(new_round_btn)

        main_layout.addLayout(header)

        self._tabs = QTabWidget()

        ward_round_tab = QWidget()
        wr_layout = QVBoxLayout(ward_round_tab)
        wr_layout.setContentsMargins(12, 12, 12, 12)

        self._rounds_table = QTableWidget()
        self._rounds_table.setColumnCount(5)
        self._rounds_table.setHorizontalHeaderLabels([
            "\u0627\u0644\u0645\u0631\u064a\u0636", "\u0627\u0644\u0637\u0628\u064a\u0628", "\u0627\u0644\u0642\u0633\u0645",
            "\u0627\u0644\u062a\u0627\u0631\u064a\u062e", "\u0627\u0644\u062d\u0627\u0644\u0629"
        ])
        self._rounds_table.horizontalHeader().setStretchLastSection(True)
        self._rounds_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._rounds_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        round_data = [
            ["\u0623\u062d\u0645\u062f \u0639\u0644\u064a", "\u062f. \u0639\u0644\u064a \u0627\u0644\u0634\u064a\u062e", "\u0627\u0644\u0637\u0648\u0627\u0631\u0626", "15/07/2026", "\u0645\u0633\u062a\u0642\u0631"],
            ["\u0645\u0631\u064a\u0645 \u062e\u0627\u0644\u062f", "\u062f. \u0646\u0648\u0631 \u0627\u0644\u062f\u064a\u0646", "\u0627\u0644\u0642\u0644\u0628", "15/07/2026", "\u0642\u064a\u062f \u0627\u0644\u0645\u0631\u0627\u0642\u0628\u0629"],
            ["\u064a\u0648\u0633\u0641 \u0645\u062d\u0645\u062f", "\u062f. \u0633\u0639\u062f \u0627\u0644\u062c\u0628\u0648\u0631\u064a", "\u0627\u0644\u062c\u0631\u0627\u062d\u0629", "14/07/2026", "\u0645\u0627 \u0628\u0639\u062f \u0627\u0644\u0639\u0645\u0644\u064a\u0629"],
        ]
        self._rounds_table.setRowCount(len(round_data))
        for i, row in enumerate(round_data):
            for j, val in enumerate(row):
                self._rounds_table.setItem(i, j, QTableWidgetItem(val))
        wr_layout.addWidget(self._rounds_table)

        self._round_form = WardRoundForm()
        self._round_form.setVisible(False)
        wr_layout.addWidget(self._round_form)

        self._tabs.addTab(ward_round_tab, self._tr.get("ward_rounds"))

        tasks_tab = QWidget()
        tasks_layout = QVBoxLayout(tasks_tab)
        tasks_layout.setContentsMargins(12, 12, 12, 12)

        task_filter_layout = QHBoxLayout()
        self._task_filter = QComboBox()
        self._task_filter.addItems(["\u062c\u0645\u064a\u0639 \u0627\u0644\u0645\u0647\u0627\u0645", "\u0645\u0647\u0627\u0645\u064a", "\u0642\u064a\u062f \u0627\u0644\u0627\u0646\u062a\u0638\u0627\u0631", "\u0645\u0643\u062a\u0645\u0644\u0629"])
        task_filter_layout.addWidget(QLabel("\u062a\u0635\u0641\u064a\u0629:"))
        task_filter_layout.addWidget(self._task_filter)
        task_filter_layout.addStretch()
        tasks_layout.addLayout(task_filter_layout)

        self._tasks_table = QTableWidget()
        self._tasks_table.setColumnCount(5)
        self._tasks_table.setHorizontalHeaderLabels([
            "\u0627\u0644\u0645\u0631\u064a\u0636", "\u0627\u0644\u0645\u0647\u0645\u0629", "\u0627\u0644\u0645\u0633\u062a\u062e\u062f\u0645", "\u0627\u0644\u0623\u0648\u0644\u0648\u064a\u0629", "\u0627\u0644\u062d\u0627\u0644\u0629"
        ])
        self._tasks_table.horizontalHeader().setStretchLastSection(True)
        self._tasks_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._tasks_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        task_data = [
            ["\u0645\u0631\u064a\u0645 \u062e\u0627\u0644\u062f", "\u0642\u064a\u0627\u0633 \u0639\u0644\u0627\u0645\u0627\u062a \u062d\u064a\u0648\u064a\u0629", "\u0645\u0645\u0631\u0636\u0629 \u0633\u0627\u0631\u0629", "\u0639\u0627\u0644\u064a\u0629", "\u0642\u064a\u062f \u0627\u0644\u0627\u0646\u062a\u0638\u0627\u0631"],
            ["\u0623\u062d\u0645\u062f \u0639\u0644\u064a", "\u062a\u063a\u064a\u064a\u0631 \u0636\u0645\u0627\u062f", "\u0645\u0645\u0631\u0636\u0629 \u0646\u0648\u0631", "\u0639\u0627\u062f\u064a\u0629", "\u0645\u0643\u062a\u0645\u0644\u0629"],
            ["\u0633\u0627\u0631\u0629 \u0639\u0628\u062f \u0627\u0644\u0644\u0647", "\u0627\u0644\u062a\u062d\u0636\u064a\u0631 \u0644\u0644\u0642\u0633\u062a\u0631\u0629", "\u0645\u0645\u0631\u0636\u0629 \u0647\u062f\u0649", "\u0639\u0627\u062c\u0644\u0629", "\u0642\u064a\u062f \u0627\u0644\u062a\u0646\u0641\u064a\u0630"],
        ]
        self._tasks_table.setRowCount(len(task_data))
        for i, row in enumerate(task_data):
            for j, val in enumerate(row):
                self._tasks_table.setItem(i, j, QTableWidgetItem(val))
        tasks_layout.addWidget(self._tasks_table)

        complete_btn = QPushButton("\u062a\u0623\u0643\u064a\u062f \u0627\u0644\u0625\u0643\u0645\u0627\u0644")
        complete_btn.clicked.connect(self._on_complete_task)
        tasks_layout.addWidget(complete_btn)

        self._tabs.addTab(tasks_tab, self._tr.get("clinical_tasks"))

        vital_tab = QWidget()
        vital_layout = QVBoxLayout(vital_tab)
        vital_layout.setContentsMargins(12, 12, 12, 12)

        vital_header = QHBoxLayout()
        vital_header.addWidget(QLabel("\u0645\u0631\u064a\u0636:"))
        self._vital_patient = QComboBox()
        self._vital_patient.addItems(["\u0623\u062d\u0645\u062f \u0639\u0644\u064a", "\u0645\u0631\u064a\u0645 \u062e\u0627\u0644\u062f", "\u064a\u0648\u0633\u0641 \u0645\u062d\u0645\u062f"])
        vital_header.addWidget(self._vital_patient)
        vital_header.addStretch()
        vital_layout.addLayout(vital_header)

        chart_row = QHBoxLayout()
        heart_chart = MiniChart()
        heart_chart.set_data([72, 75, 78, 76, 74, 73, 70])
        chart_row.addWidget(QLabel("\u0645\u0639\u062f\u0644 \u0627\u0644\u0646\u0628\u0636:"))
        chart_row.addWidget(heart_chart)

        bp_chart = MiniChart()
        bp_chart.set_data([120, 122, 125, 118, 121, 119, 117])
        chart_row.addWidget(QLabel("\u0636\u063a\u0637 \u0627\u0644\u062f\u0645:"))
        chart_row.addWidget(bp_chart)

        vital_layout.addLayout(chart_row)

        vital_form = QFormLayout()
        self._bp_systolic = QLineEdit()
        self._bp_systolic.setPlaceholderText("120")
        vital_form.addRow("\u0627\u0644\u0636\u063a\u0637 \u0627\u0644\u0627\u0646\u0642\u0628\u0627\u0636\u064a:", self._bp_systolic)
        self._bp_diastolic = QLineEdit()
        self._bp_diastolic.setPlaceholderText("80")
        vital_form.addRow("\u0627\u0644\u0636\u063a\u0637 \u0627\u0644\u0627\u0646\u0628\u0633\u0627\u0637\u064a:", self._bp_diastolic)
        self._heart_rate = QLineEdit()
        self._heart_rate.setPlaceholderText("72")
        vital_form.addRow("\u0645\u0639\u062f\u0644 \u0627\u0644\u0646\u0628\u0636:", self._heart_rate)
        self._temperature = QLineEdit()
        self._temperature.setPlaceholderText("37.0")
        vital_form.addRow("\u062f\u0631\u062c\u0629 \u0627\u0644\u062d\u0631\u0627\u0631\u0629:", self._temperature)
        self._oxygen = QLineEdit()
        self._oxygen.setPlaceholderText("98")
        vital_form.addRow("\u062a\u0634\u0628\u0639 \u0627\u0644\u0623\u0643\u0633\u062c\u064a\u0646:", self._oxygen)

        vital_layout.addLayout(vital_form)

        record_vital_btn = QPushButton("\u062a\u0633\u062c\u064a\u0644 \u0627\u0644\u0639\u0644\u0627\u0645\u0627\u062a \u0627\u0644\u062d\u064a\u0648\u064a\u0629")
        record_vital_btn.clicked.connect(lambda: AlertDialog(
            "\u062a\u0645 \u0627\u0644\u062a\u0633\u062c\u064a\u0644",
            "\u062a\u0645 \u062a\u0633\u062c\u064a\u0644 \u0627\u0644\u0639\u0644\u0627\u0645\u0627\u062a \u0627\u0644\u062d\u064a\u0648\u064a\u0629 \u0628\u0646\u062c\u0627\u062d",
            "success", parent=self,
        ).exec())
        vital_layout.addWidget(record_vital_btn)

        self._tabs.addTab(vital_tab, self._tr.get("vital_signs"))

        plan_tab = QWidget()
        plan_layout = QVBoxLayout(plan_tab)
        plan_layout.setContentsMargins(12, 12, 12, 12)

        self._plans_table = QTableWidget()
        self._plans_table.setColumnCount(4)
        self._plans_table.setHorizontalHeaderLabels([
            "\u0627\u0644\u0645\u0631\u064a\u0636", "\u0646\u0648\u0639 \u0627\u0644\u062e\u0637\u0629", "\u062a\u0627\u0631\u064a\u062e \u0627\u0644\u0628\u062f\u0621", "\u0627\u0644\u062d\u0627\u0644\u0629"
        ])
        self._plans_table.horizontalHeader().setStretchLastSection(True)
        plan_data = [
            ["\u0623\u062d\u0645\u062f \u0639\u0644\u064a", "\u062e\u0637\u0629 \u0639\u0644\u0627\u062c \u062f\u0648\u0627\u0626\u064a", "10/07/2026", "\u0646\u0634\u0637"],
            ["\u0645\u0631\u064a\u0645 \u062e\u0627\u0644\u062f", "\u062e\u0637\u0629 \u062a\u0623\u0647\u064a\u0644 \u0642\u0644\u0628\u064a", "12/07/2026", "\u0642\u064a\u062f \u0627\u0644\u0645\u0631\u0627\u062c\u0639\u0629"],
        ]
        self._plans_table.setRowCount(len(plan_data))
        for i, row in enumerate(plan_data):
            for j, val in enumerate(row):
                self._plans_table.setItem(i, j, QTableWidgetItem(val))
        plan_layout.addWidget(self._plans_table)

        self._tabs.addTab(plan_tab, self._tr.get("care_plans"))

        main_layout.addWidget(self._tabs)

    def _toggle_round_form(self):
        self._round_form.setVisible(not self._round_form.isVisible())

    def _on_complete_task(self):
        row = self._tasks_table.currentRow()
        if row >= 0:
            ConfirmDialog(
                "\u062a\u0623\u0643\u064a\u062f \u0627\u0644\u0625\u0643\u0645\u0627\u0644",
                "\u0647\u0644 \u0623\u0646\u062a \u0645\u062a\u0623\u0643\u062f \u0645\u0646 \u0625\u0643\u0645\u0627\u0644 \u0627\u0644\u0645\u0647\u0645\u0629\u061f",
                parent=self,
            ).exec()
