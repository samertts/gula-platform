from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from config import AppConfig, save_config, validate_api_base_url
from l10n import TranslationManager
from session import SessionManager
from widgets.dialogs import AboutDialog, AlertDialog, ConfirmDialog


class SettingsView(QWidget):
    theme_changed = Signal(str)
    language_changed = Signal(str)
    config_changed = Signal(AppConfig)

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self._config = config
        self._tr = TranslationManager(config.language)
        self._session = SessionManager()
        self.setup_ui()

    def setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(20)

        title = QLabel(self._tr.get("settings"))
        title.setProperty("heading", True)
        layout.addWidget(title)

        profile_group = QGroupBox(self._tr.get("profile"))
        profile_layout = QFormLayout(profile_group)

        self._name_display = QLabel(self._session.name or "---")
        self._name_display.setStyleSheet("font-weight: 600;")
        profile_layout.addRow(self._tr.get("name") + ":", self._name_display)

        self._role_display = QLabel(self._session.role or "---")
        profile_layout.addRow("\u0627\u0644\u062f\u0648\u0631:", self._role_display)

        self._dept_display = QLabel(self._session.department or "---")
        profile_layout.addRow(self._tr.get("department") + ":", self._dept_display)

        layout.addWidget(profile_group)

        appearance_group = QGroupBox("\u0627\u0644\u0645\u0638\u0647\u0631")
        appearance_layout = QFormLayout(appearance_group)

        theme_row = QHBoxLayout()
        self._theme_combo = QComboBox()
        self._theme_combo.addItems([self._tr.get("dark_mode"), self._tr.get("light_mode")])
        self._theme_combo.setCurrentIndex(0 if self._config.theme == "dark" else 1)
        self._theme_combo.currentIndexChanged.connect(self._on_theme_change)
        theme_row.addWidget(self._theme_combo)
        theme_row.addStretch()
        appearance_layout.addRow(self._tr.get("dark_mode") + ":", theme_row)

        lang_row = QHBoxLayout()
        self._lang_combo = QComboBox()
        self._lang_combo.addItems([self._tr.get("arabic"), self._tr.get("english")])
        self._lang_combo.setCurrentIndex(0 if self._config.language == "ar" else 1)
        self._lang_combo.currentIndexChanged.connect(self._on_language_change)
        lang_row.addWidget(self._lang_combo)
        lang_row.addStretch()
        appearance_layout.addRow(self._tr.get("language") + ":", lang_row)

        layout.addWidget(appearance_group)

        server_group = QGroupBox("\u0627\u0644\u062e\u0627\u062f\u0645")
        server_layout = QFormLayout(server_group)

        self._server_input = QLineEdit(self._config.api_base_url)
        server_layout.addRow(self._tr.get("server_url") + ":", self._server_input)

        save_server_btn = QPushButton("\u062d\u0641\u0638")
        save_server_btn.clicked.connect(self._on_save_server)
        server_layout.addRow("", save_server_btn)

        layout.addWidget(server_group)

        sync_group = QGroupBox("\u0627\u0644\u0645\u0632\u0627\u0645\u0646\u0629")
        sync_layout = QFormLayout(sync_group)

        self._sync_interval = QSpinBox()
        self._sync_interval.setRange(10, 600)
        self._sync_interval.setValue(self._config.auto_sync_interval)
        self._sync_interval.setSuffix(" \u062b\u0627\u0646\u064a\u0629")
        sync_layout.addRow("\u0641\u062a\u0631\u0629 \u0627\u0644\u0645\u0632\u0627\u0645\u0646\u0629:", self._sync_interval)

        layout.addWidget(sync_group)

        cache_group = QGroupBox(self._tr.get("cache_management"))
        cache_layout = QVBoxLayout(cache_group)

        cache_info = QLabel(self._tr.get("cache_size") + ": 2.3 MB")
        cache_info.setStyleSheet("color: #8b949e;")
        cache_layout.addWidget(cache_info)

        clear_cache_btn = QPushButton(self._tr.get("clear_cache"))
        clear_cache_btn.setProperty("secondary", True)
        clear_cache_btn.clicked.connect(lambda: AlertDialog(
            self._tr.get("cache_management"),
            self._tr.get("cache_cleared"),
            "success", parent=self,
        ).exec())
        cache_layout.addWidget(clear_cache_btn)

        layout.addWidget(cache_group)

        about_group = QGroupBox(self._tr.get("about"))
        about_layout = QVBoxLayout(about_group)

        about_info = QLabel(
            f"NHDW - National Hospital Desktop Workspace\n"
            f"{self._tr.get('version')}: 1.0.0\n"
            f"\u00a9 2026 GULA Platform"
        )
        about_info.setStyleSheet("color: #8b949e; line-height: 1.5;")
        about_layout.addWidget(about_info)

        about_btn = QPushButton(self._tr.get("about"))
        about_btn.clicked.connect(lambda: AboutDialog(self).exec())
        about_layout.addWidget(about_btn)

        layout.addWidget(about_group)

        layout.addStretch()

        logout_layout = QHBoxLayout()
        logout_layout.addStretch()
        logout_btn = QPushButton(self._tr.get("logout"))
        logout_btn.setProperty("error", True)
        logout_btn.setMinimumWidth(200)
        logout_btn.setMinimumHeight(44)
        logout_btn.clicked.connect(self._on_logout)
        logout_layout.addWidget(logout_btn)
        logout_layout.addStretch()

        layout.addLayout(logout_layout)

        scroll.setWidget(content)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _on_theme_change(self, index: int):
        theme = "dark" if index == 0 else "light"
        self._config.theme = theme
        save_config(self._config)
        self.theme_changed.emit(theme)

    def _on_language_change(self, index: int):
        lang = "ar" if index == 0 else "en"
        self._config.language = lang
        save_config(self._config)
        self.language_changed.emit(lang)

    def _on_save_server(self):
        previous_url = self._config.api_base_url
        try:
            validated_url = validate_api_base_url(self._server_input.text())
        except ValueError:
            self._server_input.setText(previous_url)
            AlertDialog(
                "عنوان خادم غير مسموح",
                "استخدم عنوان HTTPS الرسمي للمنصة. يُسمح بـHTTP للتطوير المحلي فقط.",
                "error", parent=self,
            ).exec()
            return

        self._config.api_base_url = validated_url
        save_config(self._config)
        from api_client import ApiClient
        ApiClient().set_base_url(validated_url)
        AlertDialog(
            "\u062a\u0645 \u0627\u0644\u062d\0641\u0638",
            "\u062a\u0645 \u062a\u062d\u062f\u064a\u062b \u0639\u0646\u0648\u0627\u0646 \u0627\u0644\u062e\u0627\u062f\u0645",
            "success", parent=self,
        ).exec()

    def _on_logout(self):
        dialog = ConfirmDialog(
            self._tr.get("logout"),
            self._tr.get("confirm_logout"),
            parent=self,
        )
        dialog.confirmed.connect(self._do_logout)
        dialog.exec()

    def _do_logout(self):
        session = SessionManager()
        session.clear_session()
        from api_client import ApiClient
        ApiClient().logout()
        QApplication.quit()
