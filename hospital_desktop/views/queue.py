from __future__ import annotations

from l10n import TranslationManager
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
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


class QueueView(QWidget):
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
        title = QLabel(self._tr.get("queue"))
        title.setProperty("heading", True)
        header.addWidget(title)

        header.addStretch()

        header.addWidget(QLabel(self._tr.get("department") + ":"))
        self._dept_combo = QComboBox()
        self._dept_combo.addItems([
            "\u062c\u0645\u064a\u0639 \u0627\u0644\u0623\u0642\u0633\u0627\u0645", "\u0627\u0644\u0637\u0648\u0627\u0631\u0626",
            "\u0627\u0644\u0639\u064a\u0627\u062f\u0627\u062a \u0627\u0644\u062e\u0627\u0631\u062c\u064a\u0629",
            "\u0627\u0644\u0623\u0634\u0639\u0629", "\u0627\u0644\u0645\u062e\u062a\u0628\u0631",
        ])
        self._dept_combo.setMinimumWidth(160)
        header.addWidget(self._dept_combo)

        header.addStretch()

        checkin_btn = QPushButton("+ " + self._tr.get("check_in"))
        checkin_btn.clicked.connect(self._on_checkin)
        header.addWidget(checkin_btn)

        main_layout.addLayout(header)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)
        stats = [
            ("\u0625\u062c\u0645\u0627\u0644\u064a \u0627\u0644\u0627\u0646\u062a\u0638\u0627\u0631", "18", "#58a6ff"),
            ("\u0641\u064a \u0627\u0644\u062e\u062f\u0645\u0629", "6", "#3fb950"),
            ("\u0645\u062a\u0648\u0633\u0637 \u0627\u0646\u062a\u0638\u0627\u0631", "12 \u062f\u0642\u064a\u0642\u0629", "#d29922"),
            ("\u062d\u0627\u0644\u0627\u062a \u0637\u0627\u0631\u0626\u0629", "3", "#f85149"),
        ]
        for label, val, color in stats:
            g = QGroupBox()
            g.setStyleSheet(f"QGroupBox {{ border: 1px solid {color}; border-radius: 8px; padding: 8px; }}")
            gl = QVBoxLayout(g)
            v = QLabel(val)
            v.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {color};")
            v.setAlignment(Qt.AlignmentFlag.AlignCenter)
            gl.addWidget(v)
            l = QLabel(label)
            l.setStyleSheet("color: #8b949e; font-size: 11px;")
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            gl.addWidget(l)
            stats_row.addWidget(g, 1)

        main_layout.addLayout(stats_row)

        self._tabs = QTabWidget()

        queue_tab = QWidget()
        queue_layout = QVBoxLayout(queue_tab)
        queue_layout.setContentsMargins(12, 12, 12, 12)

        self._queue_table = QTableWidget()
        self._queue_table.setColumnCount(7)
        self._queue_table.setHorizontalHeaderLabels([
            "#", "\u0627\u0644\u0645\u0631\u064a\u0636", "\u0627\u0644\u0623\u0648\u0644\u0648\u064a\u0629",
            "\u0648\u0642\u062a \u0627\u0644\u062a\u0633\u062c\u064a\u0644", "\u0645\u062f\u0629 \u0627\u0644\u0627\u0646\u062a\u0638\u0627\u0631",
            "\u0627\u0644\u0642\u0633\u0645", "\u0627\u0644\u062d\u0627\u0644\u0629"
        ])
        self._queue_table.horizontalHeader().setStretchLastSection(True)
        self._queue_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._queue_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        queue_data = [
            ["1", "\u0623\u062d\u0645\u062f \u0639\u0644\u064a", "\u0639\u0627\u062c\u0644", "08:30", "45 \u062f", "\u0627\u0644\u0637\u0648\u0627\u0631\u0626", "\u064a\u0646\u062a\u0638\u0631"],
            ["2", "\u0645\u0631\u064a\u0645 \u062e\u0627\u0644\u062f", "\u0639\u0627\u062f\u064a", "08:45", "30 \u062f", "\u0627\u0644\u0639\u064a\u0627\u062f\u0627\u062a", "\u064a\u0646\u062a\u0638\u0631"],
            ["3", "\u064a\u0648\u0633\u0641 \u0645\u062d\u0645\u062f", "\u0639\u0627\u062c\u0644", "09:00", "15 \u062f", "\u0627\u0644\u0637\u0648\u0627\u0631\u0626", "\u064a\u062a\u0645 \u062e\u062f\u0645\u062a\u0647"],
            ["4", "\u0633\u0627\u0631\u0629 \u0639\u0628\u062f \u0627\u0644\u0644\u0647", "\u0639\u0627\u062f\u064a", "09:15", "0 \u062f", "\u0627\u0644\u0623\u0634\u0639\u0629", "\u062c\u062f\u064a\u062f"],
            ["5", "\u0639\u0644\u064a \u062d\u0633\u0646", "\u0645\u0646\u062e\u0641\u0636", "09:30", "0 \u062f", "\u0627\u0644\u0645\u062e\u062a\u0628\u0631", "\u062c\u062f\u064a\u062f"],
            ["6", "\u0641\u0627\u0637\u0645\u0629 \u0623\u062d\u0645\u062f", "\u0639\u0627\u062f\u064a", "09:45", "0 \u062f", "\u0627\u0644\u0639\u064a\u0627\u062f\u0627\u062a", "\u062c\u062f\u064a\u062f"],
        ]
        self._queue_table.setRowCount(len(queue_data))
        for i, row in enumerate(queue_data):
            for j, val in enumerate(row):
                item = QTableWidgetItem(val)
                if j == 2 and val == "\u0639\u0627\u062c\u0644":
                    item.setForeground(QColor("#f85149"))
                self._queue_table.setItem(i, j, item)

        queue_layout.addWidget(self._queue_table)

        action_row = QHBoxLayout()
        serve_btn = QPushButton(self._tr.get("serve"))
        serve_btn.setProperty("success", True)
        serve_btn.clicked.connect(self._on_serve)
        action_row.addWidget(serve_btn)

        complete_btn = QPushButton(self._tr.get("complete"))
        complete_btn.clicked.connect(self._on_complete)
        action_row.addWidget(complete_btn)

        noshow_btn = QPushButton(self._tr.get("no_show"))
        noshow_btn.setProperty("error", True)
        noshow_btn.clicked.connect(self._on_noshow)
        action_row.addWidget(noshow_btn)

        action_row.addStretch()
        queue_layout.addLayout(action_row)

        self._tabs.addTab(queue_tab, self._tr.get("queue"))

        waiting_tab = QWidget()
        waiting_layout = QVBoxLayout(waiting_tab)
        waiting_layout.setContentsMargins(12, 12, 12, 12)

        waiting_label = QLabel("\u0642\u0627\u0626\u0645\u0629 \u0627\u0646\u062a\u0638\u0627\u0631 \u0627\u0644\u0625\u062f\u062e\u0627\u0644")
        waiting_label.setProperty("subheading", True)
        waiting_layout.addWidget(waiting_label)

        self._waiting_table = QTableWidget()
        self._waiting_table.setColumnCount(5)
        self._waiting_table.setHorizontalHeaderLabels([
            "\u0627\u0644\u0645\u0631\u064a\u0636", "\u062a\u0627\u0631\u064a\u062e \u0627\u0644\u0637\u0644\u0628",
            "\u0627\u0644\u0642\u0633\u0645 \u0627\u0644\u0645\u0637\u0644\u0648\u0628", "\u0627\u0644\u0623\u0648\u0644\u0648\u064a\u0629", "\u0627\u0644\u062d\u0627\u0644\u0629"
        ])
        self._waiting_table.horizontalHeader().setStretchLastSection(True)

        waiting_data = [
            ["\u0645\u062d\u0645\u062f \u0625\u0628\u0631\u0627\u0647\u064a\u0645", "14/07/2026", "\u0627\u0644\u0639\u0646\u0627\u064a\u0629 \u0627\u0644\u0645\u0631\u0643\u0632\u0629", "\u0639\u0627\u062c\u0644\u0629", "\u0628\u0627\u0646\u062a\u0638\u0627\u0631 \u0627\u0644\u0633\u0631\u064a\u0631"],
            ["\u0646\u0648\u0631 \u0627\u0644\u0647\u062f\u0649", "15/07/2026", "\u0627\u0644\u062c\u0631\u0627\u062d\u0629", "\u0639\u0627\u062f\u064a\u0629", "\u0628\u0627\u0646\u062a\u0638\u0627\u0631 \u0627\u0644\u0633\u0631\u064a\u0631"],
        ]
        self._waiting_table.setRowCount(len(waiting_data))
        for i, row in enumerate(waiting_data):
            for j, val in enumerate(row):
                self._waiting_table.setItem(i, j, QTableWidgetItem(val))

        waiting_layout.addWidget(self._waiting_table)

        self._tabs.addTab(waiting_tab, self._tr.get("waiting_list"))

        main_layout.addWidget(self._tabs)

    def _on_checkin(self):
        AlertDialog(
            "\u062a\u0633\u062c\u064a\u0644 \u062f\u062e\u0648\u0644",
            "\u062a\u0645 \u062a\u0633\u062c\u064a\u0644 \u062f\u062e\u0648\u0644 \u0645\u0631\u064a\u0636 \u062c\u062f\u064a\u062f",
            "info", parent=self,
        ).exec()

    def _on_serve(self):
        row = self._queue_table.currentRow()
        if row >= 0:
            self._queue_table.item(row, 6).setText("\u064a\u062a\u0645 \u062e\u062f\u0645\u062a\u0647")

    def _on_complete(self):
        row = self._queue_table.currentRow()
        if row >= 0:
            self._queue_table.item(row, 6).setText("\u0645\u0643\u062a\u0645\u0644")

    def _on_noshow(self):
        row = self._queue_table.currentRow()
        if row >= 0:
            self._queue_table.item(row, 6).setText("\u0644\u0645 \u064a\u062d\u0636\u0631")
