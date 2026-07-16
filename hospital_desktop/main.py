from __future__ import annotations

import logging
import os
import sys
import traceback

from PySide6.QtCore import QLockFile, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QSplashScreen, QWidget

from config import AppConfig, get_config_path, load_config, save_config
from session import SessionManager
from theme import ThemeManager
from widgets.dialogs import LoginDialog

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("nhdw")


def exception_hook(exc_type, exc_value, exc_tb):
    logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_tb))
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    from PySide6.QtWidgets import QMessageBox
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setWindowTitle("Unexpected Error")
    msg.setText("An unexpected error occurred. The application will continue.")
    msg.setDetailedText(tb)
    msg.exec()


def run_app(config: AppConfig):
    sys.excepthook = exception_hook

    app = QApplication(sys.argv)
    app.setApplicationName("NHDW")
    app.setOrganizationName("GULA Platform")
    app.setApplicationVersion("1.0.0")

    splash = QSplashScreen()
    splash.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
    splash.resize(400, 300)
    splash.show()
    splash.showMessage("NHDW - National Hospital Desktop Workspace\nLoading...",
                       Qt.AlignmentFlag.AlignCenter, Qt.white)
    app.processEvents()

    lock_file = QLockFile(str(get_config_path() / "instance.lock"))
    if not lock_file.tryLock(100):
        logger.warning("Another instance is already running")
        QApplication.restoreOverrideCursor()
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(None, "NHDW",
                            "Another instance of NHDW is already running.\n"
                            "Only one instance is allowed.")
        return 1

    try:
        ThemeManager.apply_theme(app, config.theme)
        app.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft if config.language == "ar"
            else Qt.LayoutDirection.LeftToRight
        )

        session = SessionManager()
        session_restored = session.load_session()

        if session_restored and session.is_authenticated:
            from api_client import ApiClient
            client = ApiClient(config.api_base_url)
            client.token = session.token
            client.refresh_token = session.refresh_token
        else:
            login_dialog = LoginDialog(config)
            if login_dialog.exec() != LoginDialog.DialogCode.Accepted:
                splash.close()
                return 0

            data = login_dialog.get_result()
            user_info = data.get("user", data.get("user_info", {}))
            token = data.get("access_token", data.get("token", ""))
            refresh_token = data.get("refresh_token", "")
            session.set_session(user_info, token, refresh_token)

        splash.close()

        from windows.main_window import MainWindow

        window = MainWindow(config)
        window.show()

        return app.exec()
    finally:
        lock_file.unlock()


def main():
    config = load_config()

    if "--theme" in sys.argv:
        idx = sys.argv.index("--theme")
        if idx + 1 < len(sys.argv):
            config.theme = sys.argv[idx + 1]
    if "--language" in sys.argv:
        idx = sys.argv.index("--language")
        if idx + 1 < len(sys.argv):
            config.language = sys.argv[idx + 1]
    if "--server" in sys.argv:
        idx = sys.argv.index("--server")
        if idx + 1 < len(sys.argv):
            config.api_base_url = sys.argv[idx + 1]
    if "--offline" in sys.argv:
        config.offline_mode = True

    save_config(config)
    sys.exit(run_app(config))


if __name__ == "__main__":
    main()
