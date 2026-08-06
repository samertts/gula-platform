from __future__ import annotations

from l10n import TranslationManager
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from session import SessionManager
from widgets.charts import SearchBar
from widgets.dialogs import AlertDialog

from config import AppConfig


class PatientRegistrationForm(QWidget):
    patient_registered = Signal(dict)

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self._config = config
        self._tr = TranslationManager(config.language)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("\u062a\u0633\u062c\u064a\u0644 \u0645\u0631\u064a\u0636 \u062c\u062f\u064a\u062f")
        title.setProperty("heading", True)
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(8)

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("\u0627\u0644\u0627\u0633\u0645 \u0628\u0627\u0644\u0643\u0627\u0645\u0644")
        form.addRow("\u0627\u0644\u0627\u0633\u0645:", self._name_input)

        self._mrn_input = QLineEdit()
        self._mrn_input.setPlaceholderText("\u0631\u0642\u0645 \u0627\u0644\u0645\u0644\u0641 \u0627\u0644\u0637\u0628\u064a")
        form.addRow("\u0631\u0642\u0645 \u0627\u0644\u0645\u0644\u0641:", self._mrn_input)

        self._phone_input = QLineEdit()
        self._phone_input.setPlaceholderText("\u0631\u0642\u0645 \u0627\u0644\u0647\u0627\u062a\u0641")
        form.addRow("\u0627\u0644\u0647\u0627\u062a\u0641:", self._phone_input)

        self._dept_combo = QComboBox()
        departments = [
            "\u0627\u0644\u0637\u0648\u0627\u0631\u0626", "\u0627\u0644\u0639\u0646\u0627\u064a\u0629 \u0627\u0644\u0645\u0631\u0643\u0632\u0629",
            "\u0627\u0644\u062c\u0631\u0627\u062d\u0629", "\u0637\u0628 \u0627\u0644\u0623\u0637\u0641\u0627\u0644",
            "\u0627\u0644\u0642\u0644\u0628", "\u0627\u0644\u0639\u0638\u0627\u0645",
            "\u0627\u0644\u0646\u0633\u0627\u0621 \u0648\u0627\u0644\u062a\u0648\u0644\u064a\u062f",
        ]
        self._dept_combo.addItems(departments)
        form.addRow("\u0627\u0644\u0642\u0633\u0645:", self._dept_combo)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton(self._tr.get("cancel"))
        cancel_btn.setProperty("secondary", True)
        cancel_btn.clicked.connect(lambda: self.setVisible(False))
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton(self._tr.get("save"))
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)
        layout.addStretch()

    def _on_save(self):
        data = {
            "name": self._name_input.text(),
            "mrn": self._mrn_input.text(),
            "phone": self._phone_input.text(),
            "department": self._dept_combo.currentText(),
        }
        self.patient_registered.emit(data)
        self._name_input.clear()
        self._mrn_input.clear()
        self._phone_input.clear()
        self.setVisible(False)


class PatientView(QWidget):
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
        title = QLabel(self._tr.get("patients"))
        title.setProperty("heading", True)
        header.addWidget(title)

        header.addStretch()

        self._search_bar = SearchBar(self._tr.get("search") + "...")
        header.addWidget(self._search_bar)

        quick_filter = QComboBox()
        quick_filter.addItems(["\u062c\u0645\u064a\u0639 \u0627\u0644\u0645\u0631\u0636\u0649", "\u0645\u0631\u0636\u0649 \u0645\u0646\u0648\u0645\u064a\u0646", "\u062e\u0631\u0648\u062c \u0627\u0644\u064a\u0648\u0645", "\u062d\u0627\u0644\u0627\u062a \u0637\u0627\u0631\u0626\u0629"])
        quick_filter.setMinimumWidth(150)
        quick_filter.currentTextChanged.connect(self._on_filter)
        header.addWidget(quick_filter)

        register_btn = QPushButton("+ " + self._tr.get("register_patient"))
        register_btn.clicked.connect(self._toggle_registration)
        header.addWidget(register_btn)

        export_btn = QPushButton(self._tr.get("export"))
        export_btn.setProperty("secondary", True)
        header.addWidget(export_btn)

        main_layout.addLayout(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)

        self._patient_table = QTableWidget()
        self._patient_table.setColumnCount(7)
        self._patient_table.setHorizontalHeaderLabels([
            "\u0631\u0642\u0645 \u0627\u0644\u0645\u0644\u0641", self._tr.get("name"), self._tr.get("age"),
            self._tr.get("gender"), self._tr.get("phone"), self._tr.get("department"), "\u0627\u0644\u062d\u0627\u0644\u0629"
        ])
        self._patient_table.horizontalHeader().setStretchLastSection(True)
        self._patient_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._patient_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._patient_table.itemSelectionChanged.connect(self._on_patient_selected)
        list_layout.addWidget(self._patient_table)

        splitter.addWidget(list_container)

        self._detail_panel = QWidget()
        detail_layout = QVBoxLayout(self._detail_panel)
        detail_layout.setContentsMargins(12, 0, 0, 0)

        detail_title = QLabel(self._tr.get("patient_info"))
        detail_title.setProperty("subheading", True)
        detail_layout.addWidget(detail_title)

        self._detail_tabs = QTabWidget()
        self._demographics_tab = QWidget()
        demo_layout = QFormLayout(self._demographics_tab)
        self._demo_labels = {}
        for field in ["\u0627\u0644\u0627\u0633\u0645", "\u0631\u0642\u0645 \u0627\u0644\u0645\u0644\u0641", self._tr.get("age"),
                       self._tr.get("gender"), self._tr.get("phone"), self._tr.get("address"),
                       self._tr.get("department"), "\u062a\u0627\u0631\u064a\u062e \u0627\u0644\u0625\u062f\u062e\u0627\u0644"]:
            label = QLabel("---")
            label.setWordWrap(True)
            demo_layout.addRow(field + ":", label)
            self._demo_labels[field] = label

        self._detail_tabs.addTab(self._demographics_tab, self._tr.get("patient_info"))

        self._encounters_tab = QTableWidget()
        self._encounters_tab.setColumnCount(4)
        self._encounters_tab.setHorizontalHeaderLabels(["\u0627\u0644\u0646\u0648\u0639", "\u0627\u0644\u0642\u0633\u0645", "\u0627\u0644\u0637\u0628\u064a\u0628", "\u0627\u0644\u062d\u0627\u0644\u0629"])
        self._encounters_tab.horizontalHeader().setStretchLastSection(True)
        self._detail_tabs.addTab(self._encounters_tab, self._tr.get("encounters"))

        detail_layout.addWidget(self._detail_tabs)

        splitter.addWidget(self._detail_panel)
        splitter.setSizes([500, 350])

        main_layout.addWidget(splitter)

        self._registration_form = PatientRegistrationForm(self._config)
        self._registration_form.setVisible(False)
        self._registration_form.patient_registered.connect(self._on_patient_registered)
        main_layout.addWidget(self._registration_form)

        self._load_sample_data()

    def _toggle_registration(self):
        self._registration_form.setVisible(not self._registration_form.isVisible())

    def _load_sample_data(self):
        patients = [
            ["1001", "\u0623\u062d\u0645\u062f \u0639\u0644\u064a", "45", "\u0630\u0643\u0631", "07701234567", "\u0627\u0644\u0637\u0648\u0627\u0631\u0626", "\u0645\u0646\u0648\u0645"],
            ["1002", "\u0645\u0631\u064a\u0645 \u062e\u0627\u0644\u062f", "32", "\u0623\u0646\u062b\u0649", "07707654321", "\u0627\u0644\u0642\u0644\u0628", "\u0645\u0646\u0648\u0645"],
            ["1003", "\u064a\u0648\u0633\u0641 \u0645\u062d\u0645\u062f", "28", "\u0630\u0643\u0631", "07801112233", "\u0627\u0644\u062c\u0631\u0627\u062d\u0629", "\u0645\u0646\u062a\u0638\u0631 \u0627\u0644\u0639\u0645\u0644\u064a\u0629"],
            ["1004", "\u0633\u0627\u0631\u0629 \u0639\u0628\u062f \u0627\u0644\u0644\u0647", "55", "\u0623\u0646\u062b\u0649", "07704445566", "\u0627\u0644\u0639\u0646\u0627\u064a\u0629 \u0627\u0644\u0645\u0631\u0643\u0632\u0629", "\u062d\u0627\u0644\u0629 \u062d\u0631\u062c\u0629"],
            ["1005", "\u0639\u0644\u064a \u062d\u0633\u0646", "8", "\u0630\u0643\u0631", "07807778899", "\u0637\u0628 \u0627\u0644\u0623\u0637\u0641\u0627\u0644", "\u0645\u0646\u0648\u0645"],
        ]
        self._patient_table.setRowCount(len(patients))
        for i, row in enumerate(patients):
            for j, val in enumerate(row):
                self._patient_table.setItem(i, j, QTableWidgetItem(val))

    def _on_patient_selected(self):
        row = self._patient_table.currentRow()
        if row < 0:
            return

        data = {
            "name": self._patient_table.item(row, 1).text() if self._patient_table.item(row, 1) else "",
            "mrn": self._patient_table.item(row, 0).text() if self._patient_table.item(row, 0) else "",
            "age": self._patient_table.item(row, 2).text() if self._patient_table.item(row, 2) else "",
            "gender": self._patient_table.item(row, 3).text() if self._patient_table.item(row, 3) else "",
            "phone": self._patient_table.item(row, 4).text() if self._patient_table.item(row, 4) else "",
            "department": self._patient_table.item(row, 5).text() if self._patient_table.item(row, 5) else "",
            "status": self._patient_table.item(row, 6).text() if self._patient_table.item(row, 6) else "",
        }

        if "\u0627\u0644\u0627\u0633\u0645" in self._demo_labels:
            self._demo_labels["\u0627\u0644\u0627\u0633\u0645"].setText(data["name"])
        if "\u0631\u0642\u0645 \u0627\u0644\u0645\u0644\u0641" in self._demo_labels:
            self._demo_labels["\u0631\u0642\u0645 \u0627\u0644\u0645\u0644\u0641"].setText(data["mrn"])
        if self._tr.get("age") in self._demo_labels:
            self._demo_labels[self._tr.get("age")].setText(data["age"])
        if self._tr.get("gender") in self._demo_labels:
            self._demo_labels[self._tr.get("gender")].setText(data["gender"])
        if self._tr.get("phone") in self._demo_labels:
            self._demo_labels[self._tr.get("phone")].setText(data["phone"])
        if self._tr.get("department") in self._demo_labels:
            self._demo_labels[self._tr.get("department")].setText(data["department"])

    def _on_filter(self, text: str):
        pass

    def _on_patient_registered(self, data: dict):
        AlertDialog("\u062a\u0645 \u0627\u0644\u062a\u0633\u062c\u064a\u0644",
                     f"\u062a\u0645 \u062a\u0633\u062c\u064a\u0644 \u0627\u0644\u0645\u0631\u064a\u0636 {data['name']} \u0628\u0646\u062c\u0627\u062d",
                     "success", parent=self).exec()
