from __future__ import annotations

from l10n import TranslationManager
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from config import AppConfig


class LoginDialog(QDialog):
    login_successful = Signal(dict)

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self._config = config
        self._tr = TranslationManager(config.language)
        self._result_data: dict = {}
        self.setup_ui()

    def setup_ui(self):
        is_ar = self._config.language == "ar"
        layout_dir = Qt.LayoutDirection.RightToLeft if is_ar else Qt.LayoutDirection.LeftToRight
        self.setLayoutDirection(layout_dir)

        self.setWindowTitle(self._tr.get("login_title"))
        self.setFixedSize(400, 480)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setObjectName("loginDialog")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 40, 32, 32)
        main_layout.setSpacing(16)

        title = QLabel("NHDW")
        title.setFont(QFont("Tahoma", 28, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setProperty("heading", True)
        main_layout.addWidget(title)

        subtitle = QLabel(self._tr.get("app_title"))
        subtitle.setFont(QFont("Tahoma", 11))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setProperty("subheading", True)
        subtitle.setWordWrap(True)
        main_layout.addWidget(subtitle)

        main_layout.addSpacing(20)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight if is_ar else Qt.AlignmentFlag.AlignLeft)

        self._server_input = QLineEdit(self._config.api_base_url)
        self._server_input.setPlaceholderText(self._tr.get("server_url"))
        self._server_input.setMinimumHeight(40)
        form.addRow(self._tr.get("server_url"), self._server_input)

        self._username_input = QLineEdit()
        self._username_input.setPlaceholderText(self._tr.get("username"))
        self._username_input.setMinimumHeight(40)
        form.addRow(self._tr.get("username"), self._username_input)

        self._password_input = QLineEdit()
        self._password_input.setPlaceholderText(self._tr.get("password"))
        self._password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._password_input.setMinimumHeight(40)
        form.addRow(self._tr.get("password"), self._password_input)

        main_layout.addLayout(form)

        self._error_label = QLabel("")
        self._error_label.setProperty("status", True)
        self._error_label.setStyleSheet("color: #f85149; font-size: 12px;")
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.setWordWrap(True)
        self._error_label.setVisible(False)
        main_layout.addWidget(self._error_label)

        main_layout.addSpacing(8)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self._cancel_btn = QPushButton(self._tr.get("cancel"))
        self._cancel_btn.setProperty("secondary", True)
        self._cancel_btn.setMinimumHeight(44)
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        self._login_btn = QPushButton(self._tr.get("login"))
        self._login_btn.setMinimumHeight(44)
        self._login_btn.clicked.connect(self._on_login)
        self._login_btn.setDefault(True)
        btn_layout.addWidget(self._login_btn)

        main_layout.addLayout(btn_layout)

        self._password_input.returnPressed.connect(self._on_login)
        main_layout.addStretch()

        if is_ar:
            self._server_input.setAlignment(Qt.AlignmentFlag.AlignRight)
            self._username_input.setAlignment(Qt.AlignmentFlag.AlignRight)
            self._password_input.setAlignment(Qt.AlignmentFlag.AlignRight)

    def _on_login(self):
        self._error_label.setVisible(False)
        self._login_btn.setEnabled(False)
        self._login_btn.setText(self._tr.get("connecting") + "...")

        from api_client import ApiClient, AuthError, NetworkError

        client = ApiClient()
        client.set_base_url(self._server_input.text().strip())

        try:
            data = client.login(
                self._username_input.text().strip(),
                self._password_input.text(),
            )
            self._result_data = data
            self.login_successful.emit(data)
            self.accept()
        except AuthError:
            self._error_label.setText(self._tr.get("login_error"))
            self._error_label.setVisible(True)
        except NetworkError:
            self._error_label.setText(self._tr.get("connection_error"))
            self._error_label.setVisible(True)
        except Exception as e:
            self._error_label.setText(str(e)[:100])
            self._error_label.setVisible(True)
        finally:
            self._login_btn.setEnabled(True)
            self._login_btn.setText(self._tr.get("login"))

    def get_result(self) -> dict:
        return self._result_data


class AlertDialog(QDialog):
    def __init__(self, title: str, message: str, dialog_type: str = "info",
                 buttons: list[str] | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self.setMinimumHeight(200)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setObjectName("alertDialog")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        icon_map = {
            "info": "\u2139\ufe0f",
            "warning": "\u26a0\ufe0f",
            "error": "\u274c",
            "success": "\u2705",
        }
        icon = icon_map.get(dialog_type, "\u2139\ufe0f")

        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI Emoji", 32))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setFont(QFont("Tahoma", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        msg_label = QLabel(message)
        msg_label.setFont(QFont("Tahoma", 11))
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        layout.addStretch()

        if buttons:
            btn_layout = QHBoxLayout()
            for btn_text in buttons:
                btn = QPushButton(btn_text)
                btn.setMinimumHeight(36)
                btn.clicked.connect(lambda checked=False, b=btn_text: self._on_click(b))
                btn_layout.addWidget(btn)
            layout.addLayout(btn_layout)
        else:
            ok_btn = QPushButton("OK")
            ok_btn.setMinimumHeight(36)
            ok_btn.clicked.connect(self.accept)
            layout.addWidget(ok_btn)

    def _on_click(self, text: str):
        self._result = text
        self.accept()

    def get_result(self) -> str:
        return getattr(self, "_result", "OK")


class ConfirmDialog(QDialog):
    confirmed = Signal()
    cancelled = Signal()

    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(380)
        self.setObjectName("confirmDialog")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title_label = QLabel(title)
        title_label.setFont(QFont("Tahoma", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg_label)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("secondary", True)
        cancel_btn.clicked.connect(self._on_cancel)
        btn_layout.addWidget(cancel_btn)

        confirm_btn = QPushButton("Confirm")
        confirm_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(confirm_btn)

        layout.addLayout(btn_layout)

    def _on_confirm(self):
        self.confirmed.emit()
        self.accept()

    def _on_cancel(self):
        self.cancelled.emit()
        self.reject()


class DateRangeDialog(QDialog):
    range_selected = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Date Range")
        self.setMinimumWidth(400)
        self.setObjectName("dateRangeDialog")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Date Range")
        title.setFont(QFont("Tahoma", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        quick_layout = QHBoxLayout()
        for label, days in [("Today", 0), ("This Week", 7), ("This Month", 30), ("This Year", 365)]:
            btn = QPushButton(label)
            btn.setProperty("secondary", True)
            btn.clicked.connect(lambda checked=False, d=days: self._quick_range(d))
            quick_layout.addWidget(btn)
        layout.addLayout(quick_layout)

        form = QFormLayout()
        self._start_date = QDateEdit()
        self._start_date.setCalendarPopup(True)
        self._start_date.setDisplayFormat("yyyy-MM-dd")
        form.addRow("From:", self._start_date)

        self._end_date = QDateEdit()
        self._end_date.setCalendarPopup(True)
        self._end_date.setDisplayFormat("yyyy-MM-dd")
        form.addRow("To:", self._end_date)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("secondary", True)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self._on_apply)
        btn_layout.addWidget(apply_btn)

        layout.addLayout(btn_layout)

    def _quick_range(self, days: int):
        from datetime import datetime, timedelta
        end = datetime.now()
        start = end - timedelta(days=days)
        self.range_selected.emit(start.isoformat(), end.isoformat())
        self.accept()

    def _on_apply(self):
        self.range_selected.emit(
            self._start_date.date().toString("yyyy-MM-dd"),
            self._end_date.date().toString("yyyy-MM-dd"),
        )
        self.accept()


class PatientSearchDialog(QDialog):
    patient_selected = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Search Patient")
        self.setMinimumSize(600, 500)
        self.setObjectName("patientSearchDialog")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        search_layout = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search by name, MRN, phone, or national ID...")
        self._search_input.setProperty("search", True)
        self._search_input.setMinimumHeight(36)
        self._search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self._search_input)

        layout.addLayout(search_layout)

        self._results_table = QTableWidget()
        self._results_table.setColumnCount(6)
        self._results_table.setHorizontalHeaderLabels(["MRN", "Name", "Age", "Gender", "Phone", "Department"])
        self._results_table.horizontalHeader().setStretchLastSection(True)
        self._results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._results_table.doubleClicked.connect(self._on_select)
        layout.addWidget(self._results_table)

        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("secondary", True)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        select_btn = QPushButton("Select")
        select_btn.clicked.connect(self._on_select)
        btn_layout.addWidget(select_btn)

        layout.addLayout(btn_layout)

    def _on_search(self, text: str):
        if len(text) < 2:
            return
        from api_client import ApiClient
        try:
            client = ApiClient()
            data = client.get("patients", {"search": text, "limit": 20})
            items = data if isinstance(data, list) else data.get("items", data.get("data", []))
            self._results_table.setRowCount(len(items))
            for i, pt in enumerate(items):
                self._results_table.setItem(i, 0, QTableWidgetItem(pt.get("mrn", "")))
                self._results_table.setItem(i, 1, QTableWidgetItem(pt.get("name_ar", pt.get("name", ""))))
                self._results_table.setItem(i, 2, QTableWidgetItem(str(pt.get("age", ""))))
                self._results_table.setItem(i, 3, QTableWidgetItem(pt.get("gender", "")))
                self._results_table.setItem(i, 4, QTableWidgetItem(pt.get("phone", "")))
                self._results_table.setItem(i, 5, QTableWidgetItem(pt.get("department", "")))
        except Exception:
            pass

    def _on_select(self):
        row = self._results_table.currentRow()
        if row >= 0:
            data = {
                "mrn": self._results_table.item(row, 0).text(),
                "name": self._results_table.item(row, 1).text(),
                "age": self._results_table.item(row, 2).text(),
                "gender": self._results_table.item(row, 3).text(),
                "phone": self._results_table.item(row, 4).text(),
                "department": self._results_table.item(row, 5).text(),
            }
            self.patient_selected.emit(data)
        self.accept()


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About NHDW")
        self.setFixedSize(400, 350)
        self.setObjectName("aboutDialog")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("NHDW")
        title.setFont(QFont("Tahoma", 28, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("National Hospital Desktop Workspace")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setProperty("subheading", True)
        layout.addWidget(subtitle)

        version = QLabel("Version 1.0.0")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

        layout.addStretch()

        copyright_label = QLabel("\u00a9 2026 GULA Platform. All rights reserved.")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copyright_label.setStyleSheet("color: #8b949e; font-size: 11px;")
        layout.addWidget(copyright_label)

        ok_btn = QPushButton("OK")
        ok_btn.setMinimumHeight(36)
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn)
