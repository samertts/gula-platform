from __future__ import annotations

from datetime import datetime

from l10n import TranslationManager
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QLabel, QPushButton, QStatusBar, QWidget
from session import SessionManager


class StatusIndicator(QWidget):
    def __init__(self, size: int = 10, parent=None):
        super().__init__(parent)
        self._color = QColor("#6e7681")
        self._size = size
        self.setFixedSize(size + 4, size + 4)

    def set_color(self, color: str):
        self._color = QColor(color)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._color)
        offset = 2
        painter.drawEllipse(offset, offset, self._size, self._size)


class StatusBarButton(QPushButton):
    clicked_signal = Signal()

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setFlat(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("QPushButton { color: #8b949e; padding: 2px 8px; font-size: 12px; }"
                           "QPushButton:hover { color: #58a6ff; }")


class StatusBar(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tr = TranslationManager()
        self.setFixedHeight(28)

        self._connection_indicator = StatusIndicator()
        self._connection_label = QLabel(self._tr.get("online"))
        self._connection_label.setStyleSheet("font-size: 12px;")

        self._sync_button = StatusBarButton("\u21bb " + self._tr.get("syncing"))
        self._sync_button.setVisible(False)

        now = datetime.now().strftime("%H:%M %p")
        from l10n import ArStrings as _
        days = [_.saturday, _.sunday, _.monday, _.tuesday, _.wednesday, _.thursday, _.friday]
        weekday = days[datetime.now().weekday()]
        self._time_label = QLabel(f"{weekday} {now}")
        self._time_label.setStyleSheet("font-size: 12px; padding: 0 12px;")

        session = SessionManager()
        self._user_label = QLabel(f"\U0001f464 {session.name or 'User'}")
        self._user_label.setStyleSheet("font-size: 12px; padding: 0 8px;")

        self._alert_button = StatusBarButton("\U0001f514 0")
        self._alert_count = 0

        self.addPermanentWidget(self._connection_indicator)
        self.addPermanentWidget(self._connection_label)
        self.addPermanentWidget(self._sync_button)
        self.addPermanentWidget(self._alert_button)
        self.addPermanentWidget(self._user_label)
        self.addPermanentWidget(self._time_label)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_time)
        self._timer.start(60000)
        self._update_time()

    def _update_time(self):
        now = datetime.now().strftime("%H:%M %p")
        from l10n import ArStrings as _
        days = [_.saturday, _.sunday, _.monday, _.tuesday, _.wednesday, _.thursday, _.friday]
        weekday = days[datetime.now().weekday()]
        self._time_label.setText(f"{weekday} {now}")

    def set_online(self, online: bool):
        color = "#3fb950" if online else "#f85149"
        text = self._tr.get("online") if online else self._tr.get("offline")
        self._connection_indicator.set_color(color)
        self._connection_label.setText(text)

    def set_syncing(self, syncing: bool):
        self._sync_button.setVisible(syncing)

    def set_alert_count(self, count: int):
        self._alert_count = count
        color = "#f85149" if count > 0 else "#8b949e"
        self._alert_button.setText(f"\U0001f514 {count}")
        self._alert_button.setStyleSheet(
            f"QPushButton {{ color: {color}; padding: 2px 8px; font-size: 12px; }}"
            f"QPushButton:hover {{ color: #58a6ff; }}"
        )

    def set_language(self, lang: str):
        self._tr.set_language(lang)
        self._connection_label.setText(self._tr.get("online"))
