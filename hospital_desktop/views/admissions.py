from __future__ import annotations

from l10n import TranslationManager
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from session import SessionManager
from widgets.dialogs import AlertDialog

from config import AppConfig


class AdmissionForm(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel("\u0625\u062f\u062e\u0627\u0644 \u0645\u0631\u064a\u0636 \u062c\u062f\u064a\u062f")
        title.setProperty("heading", True)
        layout.addWidget(title)

        form = QFormLayout()
        self._patient_search = QLineEdit()
        self._patient_search.setPlaceholderText("\u0627\u062d\u062b \u0639\u0646 \u0645\u0631\u064a\u0636 (MRN / \u0627\u0633\u0645 / \u0647\u0627\u062a\u0641)")
        form.addRow("\u0627\u0644\u0645\u0631\u064a\u0636:", self._patient_search)

        self._dept_combo = QComboBox()
        self._dept_combo.addItems([
            "\u0627\u0644\u0637\u0648\u0627\u0631\u0626", "\u0627\u0644\u0639\u0646\u0627\u064a\u0629 \u0627\u0644\u0645\u0631\u0643\u0632\u0629",
            "\u0627\u0644\u062c\u0631\u0627\u062d\u0629", "\u0637\u0628 \u0627\u0644\u0623\u0637\u0641\u0627\u0644",
            "\u0627\u0644\u0642\u0644\u0628", "\u0627\u0644\u0639\u0638\u0627\u0645",
        ])
        form.addRow("\u0627\u0644\u0642\u0633\u0645:", self._dept_combo)

        self._room_input = QLineEdit()
        form.addRow("\u0631\u0642\u0645 \u0627\u0644\u063a\u0631\u0641\u0629:", self._room_input)

        self._bed_input = QLineEdit()
        form.addRow("\u0631\u0642\u0645 \u0627\u0644\u0633\u0631\u064a\u0631:", self._bed_input)

        self._doctor_input = QLineEdit()
        form.addRow("\u0627\u0644\u0637\u0628\u064a\u0628 \u0627\u0644\u0645\u0639\u0627\u0644\u062c:", self._doctor_input)

        self._diagnosis_input = QLineEdit()
        form.addRow("\u0627\u0644\u062a\u0634\u062e\u064a\u0635:", self._diagnosis_input)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("\u0625\u0644\u063a\u0627\u0621")
        cancel_btn.setProperty("secondary", True)
        cancel_btn.clicked.connect(lambda: self.setVisible(False))
        btn_layout.addWidget(cancel_btn)

        admit_btn = QPushButton("\u062a\u0623\u0643\u064a\u062f \u0627\u0644\u0625\u062f\u062e\u0627\u0644")
        admit_btn.clicked.connect(self._on_admit)
        btn_layout.addWidget(admit_btn)

        layout.addLayout(btn_layout)
        layout.addStretch()

    def _on_admit(self):
        AlertDialog(
            "\u062a\u0645 \u0627\u0644\u0625\u062f\u062e\u0627\u0644",
            f"\u062a\u0645 \u0625\u062f\u062e\u0627\u0644 \u0627\u0644\u0645\u0631\u064a\u0636 \u0625\u0644\u0649 {self._dept_combo.currentText()}",
            "success", parent=self,
        ).exec()
        self.setVisible(False)


class AdmissionsView(QWidget):
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
        title = QLabel(self._tr.get("admissions"))
        title.setProperty("heading", True)
        header.addWidget(title)

        header.addStretch()

        self._dept_filter = QComboBox()
        self._dept_filter.addItems(["\u062c\u0645\u064a\u0639 \u0627\u0644\u0623\u0642\u0633\u0627\u0645",
                                     "\u0627\u0644\u0637\u0648\u0627\u0631\u0626", "\u0627\u0644\u0639\u0646\u0627\u064a\u0629 \u0627\u0644\u0645\u0631\u0643\u0632\u0629",
                                     "\u0627\u0644\u062c\u0631\u0627\u062d\u0629"])
        self._dept_filter.setMinimumWidth(140)
        header.addWidget(self._dept_filter)

        new_admit_btn = QPushButton("+ " + self._tr.get("admit_patient"))
        new_admit_btn.clicked.connect(self._toggle_admission_form)
        header.addWidget(new_admit_btn)

        main_layout.addLayout(header)

        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)
        stat_defs = [
            ("\u0627\u0644\u0627\u0633\u062a\u0642\u0628\u0627\u0644\u0627\u062a \u0627\u0644\u064a\u0648\u0645", "24", "#58a6ff"),
            ("\u0627\u0644\u062e\u0631\u0648\u062c \u0627\u0644\u064a\u0648\u0645", "18", "#3fb950"),
            ("\u0627\u0644\u062a\u062d\u0648\u064a\u0644\u0627\u062a \u0627\u0644\u064a\u0648\u0645", "3", "#f0883e"),
            ("\u0625\u062c\u0645\u0627\u0644\u064a \u0627\u0644\u0645\u0646\u0648\u0645\u064a\u0646", "108", "#d29922"),
        ]
        for label, value, color in stat_defs:
            group = QGroupBox()
            group.setStyleSheet(f"QGroupBox {{ border: 1px solid {color}; border-radius: 8px; padding: 12px; }}")
            gl = QVBoxLayout(group)
            v = QLabel(value)
            v.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
            v.setAlignment(Qt.AlignmentFlag.AlignCenter)
            gl.addWidget(v)
            l = QLabel(label)
            l.setStyleSheet("color: #8b949e; font-size: 11px;")
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            gl.addWidget(l)
            stats_layout.addWidget(group)

        main_layout.addLayout(stats_layout)

        self._tabs = QTabWidget()

        tables_data = {
            self._tr.get("admissions"): [
                ["1001", "\u0623\u062d\u0645\u062f \u0639\u0644\u064a", "\u0627\u0644\u0637\u0648\u0627\u0631\u0626", "A-101", "01", "15/07/2026", "\u0622\u0644\u0627\u0645 \u0635\u062f\u0631", "\u062f. \u0639\u0644\u064a"],
                ["1002", "\u0645\u0631\u064a\u0645 \u062e\u0627\u0644\u062f", "\u0627\u0644\u0642\u0644\u0628", "B-201", "05", "15/07/2026", "\u0630\u0628\u062d\u0629 \u0635\u062f\u0631\u064a\u0629", "\u062f. \u0646\u0648\u0631"],
                ["1003", "\u064a\u0648\u0633\u0641 \u0645\u062d\u0645\u062f", "\u0627\u0644\u062c\u0631\u0627\u062d\u0629", "C-301", "12", "14/07/2026", "\u0627\u0644\u062a\u0647\u0627\u0628 \u0632\u0627\u0626\u062f\u0629", "\u062f. \u0633\u0639\u062f"],
            ],
            self._tr.get("discharges"): [
                ["1004", "\u0633\u0627\u0631\u0629 \u0639\u0628\u062f \u0627\u0644\u0644\u0647", "\u0627\u0644\u0639\u0646\u0627\u064a\u0629 \u0627\u0644\u0645\u0631\u0643\u0632\u0629", "A-102", "03", "14/07/2026", "15/07/2026", "\u062a\u062d\u0633\u0646"],
                ["1005", "\u0639\u0644\u064a \u062d\u0633\u0646", "\u0637\u0628 \u0627\u0644\u0623\u0637\u0641\u0627\u0644", "B-202", "08", "10/07/2026", "15/07/2026", "\u062a\u0639\u0627\u0641\u064d"],
            ],
            self._tr.get("transfers"): [
                ["1006", "\u0641\u0627\u0637\u0645\u0629 \u0623\u062d\u0645\u062f", "\u0627\u0644\u062c\u0631\u0627\u062d\u0629", "\u0627\u0644\u0639\u0646\u0627\u064a\u0629 \u0627\u0644\u0645\u0631\u0643\u0632\u0629", "15/07/2026", "\u062a\u062f\u0647\u0648\u0631 \u0627\u0644\u062d\u0627\u0644\u0629"],
                ["1007", "\u062e\u0627\u0644\u062f \u0639\u0645\u0631", "\u0627\u0644\u0637\u0648\u0627\u0631\u0626", "\u0627\u0644\u0642\u0644\u0628", "15/07/2026", "\u0627\u062d\u062a\u064a\u0627\u062c \u0642\u0633\u062a\u0631\u0629 \u0642\u0644\u0628"],
            ],
        }

        for tab_name, data in tables_data.items():
            table = QTableWidget()
            if tab_name == self._tr.get("transfers"):
                table.setColumnCount(6)
                table.setHorizontalHeaderLabels([
                    "\u0631\u0642\u0645 \u0627\u0644\u0645\u0644\u0641", "\u0627\u0644\u0627\u0633\u0645", "\u0645\u0646 \u0642\u0633\u0645", "\u0625\u0644\u0649 \u0642\u0633\u0645",
                    "\u0627\u0644\u062a\u0627\u0631\u064a\u062e", "\u0627\u0644\u0633\u0628\u0628"
                ])
            else:
                table.setColumnCount(8)
                table.setHorizontalHeaderLabels([
                    "\u0631\u0642\u0645 \u0627\u0644\u0645\u0644\u0641", "\u0627\u0644\u0627\u0633\u0645", "\u0627\u0644\u0642\u0633\u0645",
                    "\u0627\u0644\u063a\u0631\u0641\u0629", "\u0627\u0644\u0633\u0631\u064a\u0631", "\u062a\u0627\u0631\u064a\u062e \u0627\u0644\u0625\u062f\u062e\u0627\u0644",
                    "\u0627\u0644\u062a\u0634\u062e\u064a\u0635", "\u0627\u0644\u0637\u0628\u064a\u0628"
                ])

            table.horizontalHeader().setStretchLastSection(True)
            table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

            table.setRowCount(len(data))
            for i, row in enumerate(data):
                for j, val in enumerate(row):
                    table.setItem(i, j, QTableWidgetItem(val))

            self._tabs.addTab(table, tab_name)

        main_layout.addWidget(self._tabs)

        self._admission_form = AdmissionForm()
        self._admission_form.setVisible(False)
        main_layout.addWidget(self._admission_form)

    def _toggle_admission_form(self):
        self._admission_form.setVisible(not self._admission_form.isVisible())
