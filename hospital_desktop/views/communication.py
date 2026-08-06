from __future__ import annotations

from l10n import TranslationManager
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from session import SessionManager
from widgets.dialogs import AlertDialog

from config import AppConfig


class ComposeMessageWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel("\u0643\u062a\u0627\u0628\u0629 \u0631\u0633\u0627\u0644\u0629 \u062c\u062f\u064a\u062f\u0629")
        title.setProperty("heading", True)
        layout.addWidget(title)

        form = QFormLayout()
        self._recipient = QComboBox()
        self._recipient.addItems(["\u062f. \u0639\u0644\u064a \u0627\u0644\u0634\u064a\u062e", "\u062f. \u0646\u0648\u0631 \u0627\u0644\u062f\u064a\u0646",
                                    "\u0645\u0645\u0631\u0636\u0629 \u0633\u0627\u0631\u0629", "\u0645\u0645\u0631\u0636\u0629 \u0646\u0648\u0631"])
        form.addRow("\u0625\u0644\u0649:", self._recipient)

        self._subject = QLineEdit()
        self._subject.setPlaceholderText("\u0639\u0646\u0648\u0627\u0646 \u0627\u0644\u0631\u0633\u0627\u0644\u0629")
        form.addRow("\u0627\u0644\u0645\u0648\u0636\u0648\u0639:", self._subject)

        self._body = QTextEdit()
        self._body.setPlaceholderText("\u0646\u0635 \u0627\u0644\u0631\u0633\u0627\u0644\u0629...")
        self._body.setMinimumHeight(150)
        form.addRow("\u0627\u0644\u0646\u0635:", self._body)

        layout.addLayout(form)

        send_btn = QPushButton("\u0625\u0631\u0633\u0627\u0644")
        send_btn.setMinimumHeight(40)
        send_btn.clicked.connect(lambda: AlertDialog(
            "\u062a\u0645 \u0627\u0644\u0625\u0631\u0633\u0627\u0644",
            "\u062a\u0645 \u0625\u0631\u0633\u0627\u0644 \u0627\u0644\u0631\u0633\u0627\u0644\u0629 \u0628\u0646\u062c\u0627\u062d",
            "success", parent=self,
        ).exec())
        layout.addWidget(send_btn)


class CommunicationView(QWidget):
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
        title = QLabel(self._tr.get("communication"))
        title.setProperty("heading", True)
        header.addWidget(title)
        header.addStretch()
        main_layout.addLayout(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 8, 0)

        self._tabs = QTabWidget()

        inbox_tab = QWidget()
        inbox_layout = QVBoxLayout(inbox_tab)
        inbox_layout.setContentsMargins(8, 8, 8, 8)

        self._inbox_table = QTableWidget()
        self._inbox_table.setColumnCount(4)
        self._inbox_table.setHorizontalHeaderLabels([
            "\u0645\u0646", "\u0627\u0644\u0645\u0648\u0636\u0648\u0639", "\u0627\u0644\u062a\u0627\u0631\u064a\u062e", "\u0627\u0644\u062d\u0627\u0644\u0629"
        ])
        self._inbox_table.horizontalHeader().setStretchLastSection(True)
        self._inbox_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._inbox_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        inbox_data = [
            ["\u062f. \u0639\u0644\u064a \u0627\u0644\u0634\u064a\u062e", "\u0627\u0633\u062a\u0634\u0627\u0631\u0629 \u0645\u0631\u064a\u0636 \u0642\u0644\u0628", "15/07/2026", "\u062c\u062f\u064a\u062f"],
            ["\u0645\u0645\u0631\u0636\u0629 \u0633\u0627\u0631\u0629", "\u062a\u0642\u0631\u064a\u0631 \u062d\u0627\u0644\u0629 \u0645\u0631\u064a\u0636", "14/07/2026", "\u0645\u0642\u0631\u0648\u0621"],
            ["\u062f. \u0646\u0648\u0631 \u0627\u0644\u062f\u064a\u0646", "\u062c\u062f\u0648\u0644 \u0627\u0644\u0639\u0645\u0644\u064a\u0627\u062a \u0627\u0644\u064a\u0648\u0645", "14/07/2026", "\u0645\u0642\u0631\u0648\u0621"],
        ]
        self._inbox_table.setRowCount(len(inbox_data))
        for i, row in enumerate(inbox_data):
            for j, val in enumerate(row):
                item = QTableWidgetItem(val)
                if j == 3 and val == "\u062c\u062f\u064a\u062f":
                    item.setFont(QFont("Tahoma", 10, QFont.Weight.Bold))
                self._inbox_table.setItem(i, j, item)

        inbox_layout.addWidget(self._inbox_table)
        self._tabs.addTab(inbox_tab, self._tr.get("inbox"))

        sent_tab = QWidget()
        sent_layout = QVBoxLayout(sent_tab)
        sent_layout.setContentsMargins(8, 8, 8, 8)

        self._sent_table = QTableWidget()
        self._sent_table.setColumnCount(4)
        self._sent_table.setHorizontalHeaderLabels([
            "\u0625\u0644\u0649", "\u0627\u0644\u0645\u0648\u0636\u0648\u0639", "\u0627\u0644\u062a\u0627\u0631\u064a\u062e", "\u0627\u0644\u062d\u0627\u0644\u0629"
        ])
        self._sent_table.horizontalHeader().setStretchLastSection(True)

        sent_data = [
            ["\u062f. \u0639\u0644\u064a \u0627\u0644\u0634\u064a\u062e", "\u062a\u062d\u0648\u064a\u0644 \u0645\u0631\u064a\u0636", "15/07/2026", "\u062a\u0645 \u0627\u0644\u0642\u0631\u0627\u0621\u0629"],
            ["\u0645\u0645\u0631\u0636\u0629 \u0633\u0627\u0631\u0629", "\u062a\u0639\u0644\u064a\u0645\u0627\u062a \u0639\u0646\u0627\u064a\u0629", "14/07/2026", "\u062a\u0645 \u0627\u0644\u0627\u0633\u062a\u0644\u0627\u0645"],
        ]
        self._sent_table.setRowCount(len(sent_data))
        for i, row in enumerate(sent_data):
            for j, val in enumerate(row):
                self._sent_table.setItem(i, j, QTableWidgetItem(val))

        sent_layout.addWidget(self._sent_table)
        self._tabs.addTab(sent_tab, self._tr.get("sent"))

        compose_tab = ComposeMessageWidget()
        self._tabs.addTab(compose_tab, self._tr.get("compose"))

        left_layout.addWidget(self._tabs)
        splitter.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(8, 0, 0, 0)

        alerts_group = QGroupBox(self._tr.get("alerts"))
        alerts_layout = QVBoxLayout(alerts_group)

        alert_toolbar = QHBoxLayout()
        create_alert_btn = QPushButton("+ " + self._tr.get("create"))
        create_alert_btn.clicked.connect(lambda: AlertDialog(
            "\u0625\u0646\u0634\u0627\u0621 \u062a\u0646\u0628\u064a\u0647",
            "\u062a\u0645 \u0625\u0646\u0634\u0627\u0621 \u062a\u0646\u0628\u064a\u0647 \u062c\u062f\u064a\u062f",
            "info", parent=self,
        ).exec())
        alert_toolbar.addWidget(create_alert_btn)
        alert_toolbar.addStretch()
        alerts_layout.addLayout(alert_toolbar)

        self._alerts_table = QTableWidget()
        self._alerts_table.setColumnCount(4)
        self._alerts_table.setHorizontalHeaderLabels([
            "\u0627\u0644\u0646\u0648\u0639", "\u0627\u0644\u0639\u0646\u0648\u0627\u0646",
            "\u0627\u0644\u062d\u0627\u0644\u0629", "\u0627\u0644\u0645\u0633\u062a\u0648\u0649"
        ])
        self._alerts_table.horizontalHeader().setStretchLastSection(True)

        alert_data = [
            ["\u0633\u0631\u064a\u0631\u064a", "\u062a\u062f\u0647\u0648\u0631 \u062d\u0627\u0644\u0629 \u0645\u0631\u064a\u0636 \u0627\u0644\u0642\u0644\u0628", "\u0646\u0634\u0637", "\u0639\u0627\u0644\u064a"],
            ["\u0625\u062f\u0627\u0631\u064a", "\u0646\u0642\u0635 \u0623\u0633\u0631\u0629 \u0641\u064a \u0627\u0644\u0639\u0646\u0627\u064a\u0629", "\u0642\u064a\u062f \u0627\u0644\u0645\u0639\u0627\u0644\u062c\u0629", "\u0645\u062a\u0648\u0633\u0637"],
            ["\u0645\u062e\u0628\u0631\u064a", "\u062a\u0623\u062e\u064a\u0631 \u0646\u062a\u0627\u0626\u062c \u0645\u062e\u0628\u0631", "\u062c\u062f\u064a\u062f", "\u0645\u0646\u062e\u0641\u0636"],
        ]
        self._alerts_table.setRowCount(len(alert_data))
        for i, row in enumerate(alert_data):
            for j, val in enumerate(row):
                item = QTableWidgetItem(val)
                if j == 3 and val == "\u0639\u0627\u0644\u064a":
                    item.setForeground(QColor("#f85149"))
                self._alerts_table.setItem(i, j, item)

        alerts_layout.addWidget(self._alerts_table)

        alerts_actions = QHBoxLayout()
        ack_btn = QPushButton(self._tr.get("acknowledge"))
        ack_btn.clicked.connect(lambda: AlertDialog(
            "\u062a\u0623\u0643\u064a\u062f",
            "\u062a\u0645 \u062a\u0623\u0643\u064a\u062f \u0627\u0644\u0627\u0633\u062a\u0644\u0627\u0645",
            "success", parent=self,
        ).exec())
        alerts_actions.addWidget(ack_btn)

        resolve_btn = QPushButton(self._tr.get("resolve_alert"))
        resolve_btn.setProperty("success", True)
        resolve_btn.clicked.connect(lambda: AlertDialog(
            "\u062d\u0644 \u0627\u0644\u062a\u0646\u0628\u064a\u0647",
            "\u062a\u0645 \u062d\u0644 \u0627\u0644\u062a\u0646\u0628\u064a\u0647",
            "success", parent=self,
        ).exec())
        alerts_actions.addWidget(resolve_btn)

        alerts_actions.addStretch()
        alerts_layout.addLayout(alerts_actions)

        right_layout.addWidget(alerts_group)
        splitter.addWidget(right_panel)
        splitter.setSizes([500, 350])

        main_layout.addWidget(splitter)
