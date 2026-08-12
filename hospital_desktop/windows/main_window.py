from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QByteArray, QSize, Qt, QTimer
from PySide6.QtGui import QAction, QFont, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from config import AppConfig, get_config_path, load_config, save_config
from l10n import TranslationManager
from session import SessionManager
from theme import ThemeManager
from widgets.dialogs import AboutDialog, AlertDialog, ConfirmDialog
from widgets.navbar import NavBar
from widgets.statusbar import StatusBar

VIEW_CLASSES = {}


def _import_views():
    global VIEW_CLASSES
    if VIEW_CLASSES:
        return VIEW_CLASSES
    from views.dashboard import DashboardView
    from views.patients import PatientView
    from views.admissions import AdmissionsView
    from views.queue import QueueView
    from views.clinical import ClinicalView
    from views.communication import CommunicationView
    from views.resources import ResourceView
    from views.reports import ReportsView
    from views.settings import SettingsView

    VIEW_CLASSES = {
        "dashboard": DashboardView,
        "patients": PatientView,
        "admissions": AdmissionsView,
        "queue": QueueView,
        "clinical": ClinicalView,
        "communication": CommunicationView,
        "resources": ResourceView,
        "reports": ReportsView,
        "settings": SettingsView,
    }
    return VIEW_CLASSES


logger = logging.getLogger("nhdw.main_window")


class MainWindow(QMainWindow):
    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self._config = config
        self._tr = TranslationManager(config.language)
        self._session = SessionManager()
        self._views: dict[str, QWidget] = {}
        self._report_views = _import_views()

        self.setup_window()
        self.setup_menu_bar()
        self.setup_navbar()
        self.setup_central()
        self.setup_statusbar()
        self.setup_dock_widgets()
        self.setup_tray()
        self.setup_shortcuts()
        self.restore_state()
        self.setup_session_timer()

    def setup_window(self):
        self.setWindowTitle(self._tr.get("app_title"))
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        if self._config.language == "ar":
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        ThemeManager.apply_theme(QApplication.instance(), self._config.theme)

    def setup_menu_bar(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("\u0627\u0644\u0645\u0644\u0641" if self._config.language == "ar" else "File")

        logout_action = QAction("\u062a\u0633\u062c\u064a\u0644 \u0627\u0644\u062e\u0631\u0648\u062c" if self._config.language == "ar" else "Logout", self)
        logout_action.setShortcut(QKeySequence("Ctrl+Shift+L"))
        logout_action.triggered.connect(self._on_logout)
        file_menu.addAction(logout_action)

        exit_action = QAction("\u062e\u0631\u0648\u062c" if self._config.language == "ar" else "Exit", self)
        exit_action.setShortcut(QKeySequence("Alt+F4"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = menu_bar.addMenu("\u0639\u0631\u0636" if self._config.language == "ar" else "View")

        toggle_nav_action = QAction("\u0625\u0638\u0647\u0627\u0631/\u0625\u062e\u0641\u0627\u0621 \u0627\u0644\u0634\u0631\u064a\u0637" if self._config.language == "ar" else "Toggle Navbar", self)
        toggle_nav_action.setShortcut(QKeySequence("Ctrl+\\"))
        toggle_nav_action.triggered.connect(self._toggle_navbar)
        view_menu.addAction(toggle_nav_action)

        theme_action = QAction("\u062a\u0628\u062f\u064a\u0644 \u0627\u0644\u0648\u0636\u0639" if self._config.language == "ar" else "Toggle Theme", self)
        theme_action.setShortcut(QKeySequence("Ctrl+T"))
        theme_action.triggered.connect(self._toggle_theme)
        view_menu.addAction(theme_action)

        fullscreen_action = QAction("\u0645\u0644\u0621 \u0627\u0644\u0634\u0627\u0634\u0629" if self._config.language == "ar" else "Fullscreen", self)
        fullscreen_action.setShortcut(QKeySequence("F11"))
        fullscreen_action.triggered.connect(lambda: self.setWindowState(self.windowState() ^ Qt.WindowState.WindowFullScreen))
        view_menu.addAction(fullscreen_action)

        tools_menu = menu_bar.addMenu("\u0623\u062f\u0648\u0627\u062a" if self._config.language == "ar" else "Tools")

        refresh_action = QAction("\u062a\u062d\u062f\u064a\u062b" if self._config.language == "ar" else "Refresh All", self)
        refresh_action.setShortcut(QKeySequence("F5"))
        refresh_action.triggered.connect(self._refresh_all)
        tools_menu.addAction(refresh_action)

        sync_action = QAction("\u0645\u0632\u0627\u0645\u0646\u0629" if self._config.language == "ar" else "Sync Now", self)
        sync_action.setShortcut(QKeySequence("Ctrl+S"))
        sync_action.triggered.connect(self._on_sync)
        tools_menu.addAction(sync_action)

        help_menu = menu_bar.addMenu("\u0645\u0633\u0627\u0639\u062f\u0629" if self._config.language == "ar" else "Help")

        about_action = QAction("\u062d\u0648\u0644" if self._config.language == "ar" else "About", self)
        about_action.triggered.connect(lambda: AboutDialog(self).exec())
        help_menu.addAction(about_action)

    def setup_navbar(self):
        self._navbar = NavBar(self)
        self._navbar.nav_changed.connect(self._on_nav_change)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea if self._config.language == "ar"
                           else Qt.DockWidgetArea.LeftDockWidgetArea,
                           self._navbar)

    def setup_central(self):
        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._views.clear()
        for view_id, view_cls in self._report_views.items():
            try:
                view = view_cls(self._config)
                self._views[view_id] = view
                self._stack.addWidget(view)
            except Exception as e:
                logger.warning("Failed to create view %s: %s", view_id, e)

        if "dashboard" in self._views:
            self._stack.setCurrentWidget(self._views["dashboard"])

    def setup_statusbar(self):
        self._status_bar = StatusBar(self)
        self.setStatusBar(self._status_bar)

    def setup_dock_widgets(self):
        notifications_dock = QDockWidget("\u0627\u0644\u0625\u0634\u0639\u0627\u0631\u0627\u062a" if self._config.language == "ar" else "Notifications", self)
        notifications_content = QWidget()
        notif_layout = QVBoxLayout(notifications_content)

        notif_title = QLabel("\u0622\u062e\u0631 \u0627\u0644\u0625\u0634\u0639\u0627\u0631\u0627\u062a")
        notif_layout.addWidget(notif_title)

        self._notif_list = QListWidget()
        sample_notifs = [
            "\u062a\u0645 \u0625\u062f\u062e\u0627\u0644 \u0645\u0631\u064a\u0636 \u062c\u062f\u064a\u062f \u0625\u0644\u0649 \u0627\u0644\u0637\u0648\u0627\u0631\u0626",
            "\u062a\u0645 \u062e\u0631\u0648\u062c \u0645\u0631\u064a\u0636 0042",
            "\u062a\u0646\u0628\u064a\u0647: \u062d\u0627\u0644\u0629 \u062d\u0631\u062c\u0629 \u0641\u064a \u0627\u0644\u0639\u0646\u0627\u064a\u0629",
            "\u0646\u062a\u064a\u062c\u0629 \u0645\u062e\u0628\u0631 \u0645\u062a\u0627\u062d\u0629 \u0644\u0644\u0645\u0631\u064a\u0636 0087",
        ]
        for n in sample_notifs:
            item = QListWidgetItem(n)
            item.setSizeHint(QSize(0, 36))
            self._notif_list.addItem(item)

        notif_layout.addWidget(self._notif_list)
        notifications_dock.setWidget(notifications_content)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, notifications_dock)

    def setup_tray(self):
        self._tray_icon = QSystemTrayIcon(self)
        self._tray_icon.setToolTip("NHDW - " + self._tr.get("app_title"))

        tray_menu = QMenu()
        show_action = tray_menu.addAction("\u0625\u0638\u0647\u0627\u0631" if self._config.language == "ar" else "Show")
        show_action.triggered.connect(self.show)
        quit_action = tray_menu.addAction("\u062e\u0631\u0648\u062c" if self._config.language == "ar" else "Quit")
        quit_action.triggered.connect(self.close)
        self._tray_icon.setContextMenu(tray_menu)

        if self._config.minimize_to_tray:
            self._tray_icon.show()

    def setup_shortcuts(self):
        for key, (nav_id, _) in [
            ("Ctrl+1", "dashboard"),
            ("Ctrl+2", "patients"),
            ("Ctrl+3", "admissions"),
            ("Ctrl+4", "queue"),
            ("Ctrl+5", "clinical"),
            ("Ctrl+6", "communication"),
            ("Ctrl+7", "resources"),
            ("Ctrl+8", "reports"),
            ("Ctrl+9", "settings"),
        ]:
            action = QAction(self)
            action.setShortcut(QKeySequence(key))
            action.triggered.connect(lambda checked=False, nid=nav_id: self._navbar.set_active(nid))
            self.addAction(action)

        close_action = QAction(self)
        close_action.setShortcut(QKeySequence("Escape"))
        close_action.triggered.connect(lambda: self._on_nav_change("dashboard"))
        self.addAction(close_action)

    def setup_session_timer(self):
        self._session_timer = QTimer(self)
        self._session_timer.timeout.connect(self._check_session)
        self._session_timer.start(60000)

    def _check_session(self):
        if not self._session.is_authenticated:
            return
        from api_client import ApiClient
        try:
            ApiClient().get("auth/me")
        except Exception:
            pass

    def _on_nav_change(self, nav_id: str):
        if nav_id in self._views:
            self._stack.setCurrentWidget(self._views[nav_id])
            self._navbar.set_active(nav_id)

    def _toggle_navbar(self):
        self._navbar.toggle_collapsed()

    def _toggle_theme(self):
        new_theme = "light" if self._config.theme == "dark" else "dark"
        self._config.theme = new_theme
        save_config(self._config)
        ThemeManager.apply_theme(QApplication.instance(), new_theme)

    def _refresh_all(self):
        for view in self._views.values():
            if hasattr(view, "refresh_data"):
                view.refresh_data()
        self._status_bar.set_syncing(True)
        QTimer.singleShot(2000, lambda: self._status_bar.set_syncing(False))

    def _on_sync(self):
        self._status_bar.set_syncing(True)
        QTimer.singleShot(3000, lambda: self._status_bar.set_syncing(False))

    def _on_logout(self):
        dialog = ConfirmDialog(
            self._tr.get("logout"),
            self._tr.get("confirm_logout"),
            parent=self,
        )
        dialog.confirmed.connect(self._do_logout)
        dialog.exec()

    def _do_logout(self):
        self._session.clear_session()
        from api_client import ApiClient
        ApiClient().logout()
        self.close()

    def restore_state(self):
        config_dir = get_config_path()
        geom_file = config_dir / "geometry.bin"
        state_file = config_dir / "state.bin"

        if geom_file.exists():
            self.restoreGeometry(QByteArray.fromHex(geom_file.read_bytes().hex().encode()))
        if state_file.exists():
            self.restoreState(QByteArray.fromHex(state_file.read_bytes().hex().encode()))

    def save_state(self):
        config_dir = get_config_path()
        geom_file = config_dir / "geometry.bin"
        state_file = config_dir / "state.bin"

        geom_file.write_bytes(self.saveGeometry().toHex())
        state_file.write_bytes(self.saveState().toHex())

    def closeEvent(self, event):
        if self._config.minimize_to_tray and self._tray_icon.isVisible():
            self.hide()
            event.ignore()
            return
        self.save_state()
        event.accept()
