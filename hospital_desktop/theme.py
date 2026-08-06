from __future__ import annotations

from dataclasses import dataclass, field

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


@dataclass
class Theme:
    name: str
    colors: dict[str, str] = field(default_factory=dict)


DARK_THEME: dict[str, str] = {
    "background": "#0d1117",
    "surface": "#161b22",
    "surface_alt": "#1c2333",
    "surface_hover": "#21262d",
    "primary": "#58a6ff",
    "primary_hover": "#79c0ff",
    "primary_dark": "#1f6feb",
    "secondary": "#3b82f6",
    "secondary_hover": "#60a5fa",
    "accent": "#f0883e",
    "accent_hover": "#f9a95a",
    "text_primary": "#e6edf3",
    "text_secondary": "#8b949e",
    "text_muted": "#6e7681",
    "text_disabled": "#484f58",
    "error": "#f85149",
    "error_hover": "#ff6b63",
    "error_bg": "#2d1215",
    "success": "#3fb950",
    "success_hover": "#56d364",
    "success_bg": "#12291a",
    "warning": "#d29922",
    "warning_hover": "#e3b341",
    "warning_bg": "#271c0a",
    "info": "#58a6ff",
    "info_bg": "#0c2d6b",
    "border": "#30363d",
    "border_focus": "#58a6ff",
    "card": "#161b22",
    "card_hover": "#1c2333",
    "nav": "#0d1117",
    "nav_active": "#1f6feb",
    "nav_hover": "#21262d",
    "nav_text": "#8b949e",
    "nav_text_active": "#e6edf3",
    "toolbar": "#161b22",
    "statusbar": "#0d1117",
    "input_bg": "#0d1117",
    "input_text": "#e6edf3",
    "input_placeholder": "#6e7681",
    "input_border": "#30363d",
    "input_focus": "#58a6ff",
    "table_bg": "#0d1117",
    "table_alt": "#161b22",
    "table_border": "#30363d",
    "table_header": "#1c2333",
    "scrollbar": "#30363d",
    "scrollbar_hover": "#484f58",
    "divider": "#21262d",
    "shadow": "rgba(0,0,0,0.4)",
    "overlay": "rgba(0,0,0,0.6)",
    "badge": "#f85149",
    "badge_text": "#ffffff",
    "chart_line": "#58a6ff",
    "chart_fill": "rgba(31,111,235,0.2)",
    "chart_grid": "#21262d",
    "chart_label": "#8b949e",
    "kpi_card": "#161b22",
    "kpi_value": "#e6edf3",
    "kpi_label": "#8b949e",
    "progress_fill": "#1f6feb",
    "progress_bg": "#21262d",
    "tab_active": "#1f6feb",
    "tab_inactive": "#161b22",
    "tab_hover": "#21262d",
    "tooltip_bg": "#1c2333",
    "tooltip_text": "#e6edf3",
    "menu_bg": "#161b22",
    "menu_hover": "#21262d",
    "menu_separator": "#30363d",
    "dock_title": "#8b949e",
    "dock_bg": "#0d1117",
    "tray_icon": "#e6edf3",
    "online": "#3fb950",
    "offline": "#f85149",
    "syncing": "#d29922",
}

LIGHT_THEME: dict[str, str] = {
    "background": "#ffffff",
    "surface": "#f6f8fa",
    "surface_alt": "#eaeef2",
    "surface_hover": "#eaeef2",
    "primary": "#0969da",
    "primary_hover": "#0550ae",
    "primary_dark": "#0550ae",
    "secondary": "#2563eb",
    "secondary_hover": "#1d4ed8",
    "accent": "#d4760a",
    "accent_hover": "#b85e00",
    "text_primary": "#1f2328",
    "text_secondary": "#656d76",
    "text_muted": "#8b949e",
    "text_disabled": "#afb8c1",
    "error": "#cf222e",
    "error_hover": "#a40e26",
    "error_bg": "#ffebe9",
    "success": "#1a7f37",
    "success_hover": "#116329",
    "success_bg": "#dafbe1",
    "warning": "#9a6700",
    "warning_hover": "#7f4f00",
    "warning_bg": "#fff8c5",
    "info": "#0969da",
    "info_bg": "#ddf4ff",
    "border": "#d0d7de",
    "border_focus": "#0969da",
    "card": "#ffffff",
    "card_hover": "#f6f8fa",
    "nav": "#ffffff",
    "nav_active": "#0969da",
    "nav_hover": "#f6f8fa",
    "nav_text": "#656d76",
    "nav_text_active": "#1f2328",
    "toolbar": "#f6f8fa",
    "statusbar": "#ffffff",
    "input_bg": "#ffffff",
    "input_text": "#1f2328",
    "input_placeholder": "#8b949e",
    "input_border": "#d0d7de",
    "input_focus": "#0969da",
    "table_bg": "#ffffff",
    "table_alt": "#f6f8fa",
    "table_border": "#d0d7de",
    "table_header": "#eaeef2",
    "scrollbar": "#d0d7de",
    "scrollbar_hover": "#afb8c1",
    "divider": "#d0d7de",
    "shadow": "rgba(0,0,0,0.1)",
    "overlay": "rgba(0,0,0,0.3)",
    "badge": "#cf222e",
    "badge_text": "#ffffff",
    "chart_line": "#0969da",
    "chart_fill": "rgba(9,105,218,0.15)",
    "chart_grid": "#d0d7de",
    "chart_label": "#656d76",
    "kpi_card": "#ffffff",
    "kpi_value": "#1f2328",
    "kpi_label": "#656d76",
    "progress_fill": "#0969da",
    "progress_bg": "#d0d7de",
    "tab_active": "#0969da",
    "tab_inactive": "#ffffff",
    "tab_hover": "#f6f8fa",
    "tooltip_bg": "#1f2328",
    "tooltip_text": "#ffffff",
    "menu_bg": "#ffffff",
    "menu_hover": "#f6f8fa",
    "menu_separator": "#d0d7de",
    "dock_title": "#656d76",
    "dock_bg": "#ffffff",
    "tray_icon": "#1f2328",
    "online": "#1a7f37",
    "offline": "#cf222e",
    "syncing": "#9a6700",
}

THEMES = {
    "dark": Theme(name="dark", colors=DARK_THEME),
    "light": Theme(name="light", colors=LIGHT_THEME),
}


class ThemeManager:

    @staticmethod
    def get_theme(name: str) -> Theme:
        return THEMES.get(name, THEMES["dark"])

    @staticmethod
    def apply_theme(app: QApplication, theme_name: str):
        theme = ThemeManager.get_theme(theme_name)
        colors = theme.colors

        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(colors["background"]))
        palette.setColor(QPalette.WindowText, QColor(colors["text_primary"]))
        palette.setColor(QPalette.Base, QColor(colors["input_bg"]))
        palette.setColor(QPalette.AlternateBase, QColor(colors["surface"]))
        palette.setColor(QPalette.ToolTipBase, QColor(colors["tooltip_bg"]))
        palette.setColor(QPalette.ToolTipText, QColor(colors["tooltip_text"]))
        palette.setColor(QPalette.Text, QColor(colors["input_text"]))
        palette.setColor(QPalette.Button, QColor(colors["surface"]))
        palette.setColor(QPalette.ButtonText, QColor(colors["text_primary"]))
        palette.setColor(QPalette.BrightText, QColor(colors["error"]))
        palette.setColor(QPalette.Link, QColor(colors["primary"]))
        palette.setColor(QPalette.Highlight, QColor(colors["primary"]))
        palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(colors["text_disabled"]))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(colors["text_disabled"]))

        app.setPalette(palette)
        app.setStyleSheet(ThemeManager.generate_stylesheet(theme))

    @staticmethod
    def generate_stylesheet(theme: Theme) -> str:
        c = theme.colors
        is_dark = theme.name == "dark"
        scrollbar_w = "8px"

        return f"""
        QMainWindow {{
            background-color: {c["background"]};
        }}
        QWidget {{
            background-color: {c["background"]};
            color: {c["text_primary"]};
            font-family: "Segoe UI", "Tahoma", "Arial", sans-serif;
            font-size: 13px;
        }}
        QLabel {{
            color: {c["text_primary"]};
            background: transparent;
            border: none;
            padding: 2px;
        }}
        QLabel[heading="true"] {{
            font-size: 20px;
            font-weight: 700;
            color: {c["text_primary"]};
        }}
        QLabel[subheading="true"] {{
            font-size: 15px;
            font-weight: 600;
            color: {c["text_secondary"]};
        }}
        QLabel[value="true"] {{
            font-size: 28px;
            font-weight: 700;
            color: {c["kpi_value"]};
        }}
        QLabel[status="true"] {{
            font-size: 12px;
            font-weight: 500;
            padding: 2px 8px;
            border-radius: 10px;
        }}
        QPushButton {{
            background-color: {c["primary"]};
            color: #ffffff;
            border: none;
            border-radius: 6px;
            padding: 8px 18px;
            font-size: 13px;
            font-weight: 600;
            min-height: 20px;
        }}
        QPushButton:hover {{
            background-color: {c["primary_hover"]};
        }}
        QPushButton:pressed {{
            background-color: {c["primary_dark"]};
        }}
        QPushButton:disabled {{
            background-color: {c["surface_hover"]};
            color: {c["text_disabled"]};
        }}
        QPushButton[secondary="true"] {{
            background-color: transparent;
            color: {c["primary"]};
            border: 1px solid {c["border"]};
        }}
        QPushButton[secondary="true"]:hover {{
            background-color: {c["surface_hover"]};
            border-color: {c["primary"]};
        }}
        QPushButton[error="true"] {{
            background-color: {c["error"]};
        }}
        QPushButton[error="true"]:hover {{
            background-color: {c["error_hover"]};
        }}
        QPushButton[success="true"] {{
            background-color: {c["success"]};
        }}
        QPushButton[success="true"]:hover {{
            background-color: {c["success_hover"]};
        }}
        QPushButton[icon="true"] {{
            background: transparent;
            border: none;
            padding: 6px;
            border-radius: 4px;
            min-width: 32px;
            min-height: 32px;
        }}
        QPushButton[icon="true"]:hover {{
            background-color: {c["surface_hover"]};
        }}
        QLineEdit {{
            background-color: {c["input_bg"]};
            color: {c["input_text"]};
            border: 1px solid {c["input_border"]};
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 13px;
            selection-background-color: {c["primary"]};
            selection-color: #ffffff;
        }}
        QLineEdit:focus {{
            border-color: {c["input_focus"]};
        }}
        QLineEdit:disabled {{
            background-color: {c["surface"]};
            color: {c["text_disabled"]};
        }}
        QLineEdit[search="true"] {{
            padding-left: 32px;
            border-radius: 20px;
        }}
        QTextEdit, QPlainTextEdit {{
            background-color: {c["input_bg"]};
            color: {c["input_text"]};
            border: 1px solid {c["input_border"]};
            border-radius: 6px;
            padding: 8px;
            font-size: 13px;
            selection-background-color: {c["primary"]};
            selection-color: #ffffff;
        }}
        QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {c["input_focus"]};
        }}
        QComboBox {{
            background-color: {c["input_bg"]};
            color: {c["input_text"]};
            border: 1px solid {c["input_border"]};
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 13px;
            min-height: 20px;
        }}
        QComboBox:hover {{
            border-color: {c["primary"]};
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 28px;
            border-left: 1px solid {c["input_border"]};
            border-top-right-radius: 6px;
            border-bottom-right-radius: 6px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {c["surface"]};
            color: {c["text_primary"]};
            border: 1px solid {c["border"]};
            border-radius: 6px;
            selection-background-color: {c["primary"]};
            selection-color: #ffffff;
            outline: none;
        }}
        QComboBox::item {{
            padding: 8px 12px;
        }}
        QComboBox::item:hover {{
            background-color: {c["surface_hover"]};
        }}
        QCheckBox {{
            spacing: 8px;
            color: {c["text_primary"]};
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 1px solid {c["input_border"]};
            border-radius: 4px;
            background-color: {c["input_bg"]};
        }}
        QCheckBox::indicator:checked {{
            background-color: {c["primary"]};
            border-color: {c["primary"]};
        }}
        QCheckBox::indicator:hover {{
            border-color: {c["primary"]};
        }}
        QRadioButton {{
            spacing: 8px;
            color: {c["text_primary"]};
        }}
        QRadioButton::indicator {{
            width: 18px;
            height: 18px;
            border: 1px solid {c["input_border"]};
            border-radius: 10px;
            background-color: {c["input_bg"]};
        }}
        QRadioButton::indicator:checked {{
            background-color: {c["primary"]};
            border-color: {c["primary"]};
        }}
        QSpinBox, QDateEdit {{
            background-color: {c["input_bg"]};
            color: {c["input_text"]};
            border: 1px solid {c["input_border"]};
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 13px;
            min-height: 20px;
        }}
        QSpinBox:focus, QDateEdit:focus {{
            border-color: {c["input_focus"]};
        }}
        QSpinBox::up-button, QDateEdit::up-button {{
            subcontrol-origin: border;
            subcontrol-position: top right;
            width: 24px;
            border-left: 1px solid {c["input_border"]};
            border-bottom: 1px solid {c["input_border"]};
        }}
        QSpinBox::down-button, QDateEdit::down-button {{
            subcontrol-origin: border;
            subcontrol-position: bottom right;
            width: 24px;
            border-left: 1px solid {c["input_border"]};
        }}
        QTableWidget {{
            background-color: {c["table_bg"]};
            color: {c["text_primary"]};
            border: 1px solid {c["table_border"]};
            border-radius: 6px;
            gridline-color: {c["table_border"]};
            selection-background-color: {c["primary_dark"]};
            selection-color: #ffffff;
            font-size: 13px;
        }}
        QTableWidget::item {{
            padding: 6px 10px;
            border-bottom: 1px solid {c["table_border"]};
        }}
        QTableWidget::item:selected {{
            background-color: {c["primary_dark"]};
            color: #ffffff;
        }}
        QTableWidget::item:hover {{
            background-color: {c["surface_hover"]};
        }}
        QHeaderView {{
            background-color: {c["table_header"]};
            border: none;
        }}
        QHeaderView::section {{
            background-color: {c["table_header"]};
            color: {c["text_secondary"]};
            padding: 8px 10px;
            border: none;
            border-bottom: 1px solid {c["table_border"]};
            border-right: 1px solid {c["table_border"]};
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
        }}
        QHeaderView::section:hover {{
            background-color: {c["surface_hover"]};
            color: {c["text_primary"]};
        }}
        QTreeWidget {{
            background-color: {c["table_bg"]};
            color: {c["text_primary"]};
            border: 1px solid {c["table_border"]};
            border-radius: 6px;
            outline: none;
        }}
        QTreeWidget::item {{
            padding: 6px 8px;
            border-bottom: 1px solid {c["table_border"]};
        }}
        QTreeWidget::item:selected {{
            background-color: {c["primary_dark"]};
            color: #ffffff;
        }}
        QTreeWidget::item:hover {{
            background-color: {c["surface_hover"]};
        }}
        QListWidget {{
            background-color: {c["table_bg"]};
            color: {c["text_primary"]};
            border: 1px solid {c["table_border"]};
            border-radius: 6px;
            outline: none;
        }}
        QListWidget::item {{
            padding: 8px 12px;
            border-bottom: 1px solid {c["table_border"]};
        }}
        QListWidget::item:selected {{
            background-color: {c["primary_dark"]};
            color: #ffffff;
        }}
        QListWidget::item:hover {{
            background-color: {c["surface_hover"]};
        }}
        QTabWidget::pane {{
            background-color: {c["background"]};
            border: 1px solid {c["border"]};
            border-top: none;
            border-radius: 0 0 6px 6px;
        }}
        QTabBar::tab {{
            background-color: {c["tab_inactive"]};
            color: {c["text_secondary"]};
            padding: 10px 20px;
            border: 1px solid {c["border"]};
            border-bottom: none;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            margin-right: 2px;
            font-weight: 500;
        }}
        QTabBar::tab:selected {{
            background-color: {c["background"]};
            color: {c["text_primary"]};
            border-bottom: 2px solid {c["tab_active"]};
            font-weight: 600;
        }}
        QTabBar::tab:hover:!selected {{
            background-color: {c["tab_hover"]};
            color: {c["text_primary"]};
        }}
        QGroupBox {{
            background-color: {c["card"]};
            border: 1px solid {c["border"]};
            border-radius: 8px;
            margin-top: 16px;
            padding: 16px;
            padding-top: 24px;
            font-weight: 600;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 4px 12px;
            color: {c["text_primary"]};
            font-weight: 600;
        }}
        QSplitter::handle {{
            background-color: {c["border"]};
            width: 1px;
        }}
        QSplitter::handle:hover {{
            background-color: {c["primary"]};
        }}
        QDockWidget {{
            background-color: {c["dock_bg"]};
            color: {c["text_primary"]};
            titlebar-close-icon: none;
            titlebar-normal-icon: none;
        }}
        QDockWidget::title {{
            background-color: {c["toolbar"]};
            color: {c["dock_title"]};
            padding: 8px 12px;
            border-bottom: 1px solid {c["border"]};
            font-weight: 600;
            font-size: 12px;
        }}
        QStatusBar {{
            background-color: {c["statusbar"]};
            color: {c["text_secondary"]};
            border-top: 1px solid {c["border"]};
            font-size: 12px;
            padding: 2px 8px;
        }}
        QStatusBar::item {{
            border: none;
        }}
        QStatusBar QLabel {{
            color: {c["text_secondary"]};
            background: transparent;
            padding: 2px 8px;
            font-size: 12px;
        }}
        QMenuBar {{
            background-color: {c["nav"]};
            color: {c["text_primary"]};
            border-bottom: 1px solid {c["border"]};
            padding: 2px 0;
        }}
        QMenuBar::item {{
            padding: 8px 14px;
            background: transparent;
            border-radius: 4px;
        }}
        QMenuBar::item:selected {{
            background-color: {c["menu_hover"]};
        }}
        QMenu {{
            background-color: {c["menu_bg"]};
            color: {c["text_primary"]};
            border: 1px solid {c["border"]};
            border-radius: 8px;
            padding: 4px;
        }}
        QMenu::item {{
            padding: 8px 32px 8px 16px;
            border-radius: 4px;
        }}
        QMenu::item:selected {{
            background-color: {c["menu_hover"]};
            color: {c["text_primary"]};
        }}
        QMenu::item:disabled {{
            color: {c["text_disabled"]};
        }}
        QMenu::separator {{
            height: 1px;
            background: {c["menu_separator"]};
            margin: 4px 8px;
        }}
        QToolBar {{
            background-color: {c["toolbar"]};
            color: {c["text_primary"]};
            border: none;
            border-bottom: 1px solid {c["border"]};
            padding: 4px;
            spacing: 4px;
        }}
        QToolBar QToolButton {{
            background: transparent;
            color: {c["text_secondary"]};
            border: none;
            border-radius: 4px;
            padding: 6px 10px;
        }}
        QToolBar QToolButton:hover {{
            background-color: {c["surface_hover"]};
            color: {c["text_primary"]};
        }}
        QToolBar QToolButton:checked {{
            background-color: {c["nav_active"]};
            color: #ffffff;
        }}
        QScrollBar:vertical {{
            background-color: transparent;
            width: {scrollbar_w};
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background-color: {c["scrollbar"]};
            border-radius: 4px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {c["scrollbar_hover"]};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QScrollBar:horizontal {{
            background-color: transparent;
            height: {scrollbar_w};
            margin: 0;
        }}
        QScrollBar::handle:horizontal {{
            background-color: {c["scrollbar"]};
            border-radius: 4px;
            min-width: 30px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background-color: {c["scrollbar_hover"]};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
        }}
        QProgressBar {{
            background-color: {c["progress_bg"]};
            border: none;
            border-radius: 4px;
            text-align: center;
            height: 8px;
            font-size: 10px;
        }}
        QProgressBar::chunk {{
            background-color: {c["progress_fill"]};
            border-radius: 4px;
        }}
        QSlider::groove:horizontal {{
            background-color: {c["progress_bg"]};
            height: 6px;
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background-color: {c["primary"]};
            width: 18px;
            height: 18px;
            margin: -6px 0;
            border-radius: 9px;
        }}
        QSlider::handle:horizontal:hover {{
            background-color: {c["primary_hover"]};
        }}
        QSlider::sub-page:horizontal {{
            background-color: {c["primary"]};
            border-radius: 3px;
        }}
        QToolTip {{
            background-color: {c["tooltip_bg"]};
            color: {c["tooltip_text"]};
            border: 1px solid {c["border"]};
            border-radius: 4px;
            padding: 6px 10px;
            font-size: 12px;
        }}
        QFrame[card="true"] {{
            background-color: {c["card"]};
            border: 1px solid {c["border"]};
            border-radius: 8px;
        }}
        QFrame[kpi="true"] {{
            background-color: {c["kpi_card"]};
            border: 1px solid {c["border"]};
            border-radius: 10px;
            padding: 16px;
        }}
        """
