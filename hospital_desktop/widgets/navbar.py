from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from session import SessionManager

NAV_ITEMS = [
    {
        "id": "dashboard",
        "icon": "\uf080",
        "icon_ar": "\ue905",
        "roles": ["*"],
    },
    {
        "id": "patients",
        "icon": "\uf0c0",
        "icon_ar": "\ue904",
        "roles": ["doctor", "nurse", "administrator", "receptionist", "technician"],
    },
    {
        "id": "admissions",
        "icon": "\uf234",
        "icon_ar": "\ue900",
        "roles": ["administrator", "receptionist", "doctor"],
    },
    {
        "id": "queue",
        "icon": "\uf0cb",
        "icon_ar": "\ue903",
        "roles": ["*"],
    },
    {
        "id": "clinical",
        "icon": "\uf21e",
        "icon_ar": "\ue901",
        "roles": ["doctor", "nurse", "technician"],
    },
    {
        "id": "communication",
        "icon": "\uf0e0",
        "icon_ar": "\ue906",
        "roles": ["*"],
    },
    {
        "id": "resources",
        "icon": "\uf013",
        "icon_ar": "\ue907",
        "roles": ["administrator"],
    },
    {
        "id": "reports",
        "icon": "\uf200",
        "icon_ar": "\ue902",
        "roles": ["doctor", "administrator"],
    },
    {
        "id": "settings",
        "icon": "\uf141",
        "icon_ar": "\ue908",
        "roles": ["*"],
    },
]

NAV_LABELS = {
    "dashboard": {"ar": "لوحة التحكم", "en": "Dashboard"},
    "patients": {"ar": "المرضى", "en": "Patients"},
    "admissions": {"ar": "الاستقبال", "en": "ADT"},
    "queue": {"ar": "طابور الانتظار", "en": "Queue"},
    "clinical": {"ar": "المهام السريرية", "en": "Clinical"},
    "communication": {"ar": "الاتصالات", "en": "Comm."},
    "resources": {"ar": "الموارد", "en": "Resources"},
    "reports": {"ar": "التقارير", "en": "Reports"},
    "settings": {"ar": "الإعدادات", "en": "Settings"},
}

NAV_ICONS = {
    "dashboard": "\U0001f4ca",
    "patients": "\U0001f465",
    "admissions": "\U0001f3e5",
    "queue": "\U0001f4cb",
    "clinical": "\U0001f3e5",
    "communication": "\U0001f4e8",
    "resources": "\U0001f527",
    "reports": "\U0001f4c4",
    "settings": "\u2699\ufe0f",
}


class NavButton(QPushButton):
    def __init__(self, nav_id: str, icon: str, label: str, parent=None):
        super().__init__(parent)
        self.nav_id = nav_id
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(44)
        self.setMaximumHeight(44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(10)

        self._icon_label = QLabel(icon)
        self._icon_label.setFixedWidth(24)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont("Segoe UI Emoji", 14)
        self._icon_label.setFont(font)
        layout.addWidget(self._icon_label)

        self._label = QLabel(label)
        self._label.setFont(QFont("Tahoma", 10, QFont.Weight.Medium))
        layout.addWidget(self._label)

        layout.addStretch()
        self.setLayout(layout)

    def set_collapsed(self, collapsed: bool):
        self._label.setVisible(not collapsed)
        if collapsed:
            self.setMinimumWidth(48)
            self.setMaximumWidth(48)
        else:
            self.setMinimumWidth(160)
            self.setMaximumWidth(220)


class NavBar(QWidget):
    nav_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._collapsed = False
        self._language = "ar"
        self._buttons: dict[str, NavButton] = {}
        self._active_id = "dashboard"

        self.setObjectName("navBar")
        self.setFixedWidth(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(2)

        app_label = QLabel("NHDW")
        app_label.setFont(QFont("Tahoma", 16, QFont.Weight.Bold))
        app_label.setProperty("heading", True)
        app_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_label.setFixedHeight(50)
        layout.addWidget(app_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        scroll_content = QWidget()
        self._nav_layout = QVBoxLayout(scroll_content)
        self._nav_layout.setContentsMargins(0, 0, 0, 0)
        self._nav_layout.setSpacing(2)
        self._nav_layout.addStretch()

        session = SessionManager()
        for item in NAV_ITEMS:
            roles = item["roles"]
            if "*" not in roles and session.role not in roles:
                continue

            nav_id = item["id"]
            icon = NAV_ICONS.get(nav_id, "\u25cf")
            label = NAV_LABELS[nav_id].get(self._language, nav_id)

            btn = NavButton(nav_id, icon, label)
            btn.clicked.connect(lambda checked=False, nid=nav_id: self._on_nav_click(nid))
            self._buttons[nav_id] = btn
            self._nav_layout.insertWidget(self._nav_layout.count() - 1, btn)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        self.setLayout(layout)
        self._update_active()

    def _on_nav_click(self, nav_id: str):
        self.set_active(nav_id)
        self.nav_changed.emit(nav_id)

    def set_active(self, nav_id: str):
        self._active_id = nav_id
        self._update_active()

    def _update_active(self):
        for btn_id, btn in self._buttons.items():
            btn.setChecked(btn_id == self._active_id)
            if btn_id == self._active_id:
                btn.setProperty("active", True)
                btn.style().unpolish(btn)
                btn.style().polish(btn)
            else:
                btn.setProperty("active", False)
                btn.style().unpolish(btn)
                btn.style().polish(btn)

    def set_language(self, lang: str):
        self._language = lang
        for nav_id, btn in self._buttons.items():
            label = NAV_LABELS[nav_id].get(lang, nav_id)
            btn._label.setText(label)

    def set_collapsed(self, collapsed: bool):
        self._collapsed = collapsed
        width = 56 if collapsed else 220
        self.setFixedWidth(width)
        for btn in self._buttons.values():
            btn.set_collapsed(collapsed)

    def toggle_collapsed(self):
        self.set_collapsed(not self._collapsed)
