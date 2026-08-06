from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QCursor,
    QFont,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class KpiCard(QFrame):
    clicked = Signal(str)

    def __init__(self, icon: str, label: str, value: str = "---",
                 trend: str = "", color: str = "#58a6ff", parent=None):
        super().__init__(parent)
        self._kpi_id = label
        self.setProperty("kpi", True)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMinimumSize(160, 100)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        header = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI Emoji", 18))
        icon_label.setStyleSheet(f"color: {color};")
        header.addWidget(icon_label)

        if trend:
            trend_label = QLabel(trend)
            is_up = trend.startswith("\u25b2") or trend.startswith("+")
            trend_color = "#3fb950" if is_up else "#f85149"
            trend_label.setStyleSheet(f"color: {trend_color}; font-size: 11px; font-weight: 600;")
            trend_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            header.addStretch()
            header.addWidget(trend_label)

        layout.addLayout(header)

        self._value_label = QLabel(value)
        self._value_label.setProperty("value", True)
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._value_label)

        self._label_label = QLabel(label)
        self._label_label.setProperty("subheading", True)
        self._label_label.setStyleSheet("font-size: 11px; color: #8b949e;")
        layout.addWidget(self._label_label)

    def set_value(self, value: str, trend: str = ""):
        self._value_label.setText(value)

    def set_trend(self, trend: str):
        pass


class MiniChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[float] = []
        self._chart_type = "line"
        self._line_color = QColor("#58a6ff")
        self._fill_color = QColor(31, 111, 235, 40)
        self._grid_color = QColor("#21262d")
        self.setMinimumSize(200, 80)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_data(self, data: list[float]):
        self._data = data
        self.update()

    def paintEvent(self, event):
        if not self._data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        margin = 4
        plot_w = w - 2 * margin
        plot_h = h - 2 * margin

        data_min = min(self._data)
        data_max = max(self._data)
        data_range = data_max - data_min if data_max != data_min else 1

        n = len(self._data)
        if n < 2:
            return

        points: list[QPointF] = []
        for i, val in enumerate(self._data):
            x = margin + (i / (n - 1)) * plot_w
            y = margin + plot_h - ((val - data_min) / data_range) * plot_h
            points.append(QPointF(x, y))

        path = QPainterPath()
        path.moveTo(points[0])
        for pt in points[1:]:
            path.lineTo(pt)

        painter.setPen(QPen(self._line_color, 2))
        painter.drawPath(path)

        fill_path = QPainterPath(path)
        fill_path.lineTo(points[-1].x(), margin + plot_h)
        fill_path.lineTo(points[0].x(), margin + plot_h)
        fill_path.closeSubpath()
        painter.fillPath(fill_path, self._fill_color)

        painter.setPen(QPen(self._grid_color, 1, Qt.PenStyle.DotLine))
        for y_pos in [margin + plot_h * 0.25, margin + plot_h * 0.5, margin + plot_h * 0.75]:
            painter.drawLine(QPointF(margin, y_pos), QPointF(margin + plot_w, y_pos))


class OccupancyGauge(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0.0
        self._label = ""
        self.setMinimumSize(140, 140)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_value(self, value: float, label: str = ""):
        self._value = max(0.0, min(100.0, value))
        self._label = label
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        side = min(w, h)
        center = QPointF(w / 2, h / 2)
        outer_r = side * 0.42
        inner_r = side * 0.32

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#21262d"))
        painter.drawEllipse(center, outer_r, outer_r)

        if self._value > 0:
            span = (self._value / 100.0) * 360.0
            start = 135.0

            if self._value < 60:
                color = QColor("#3fb950")
            elif self._value < 85:
                color = QColor("#d29922")
            else:
                color = QColor("#f85149")

            painter.setPen(QPen(color, 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawArc(
                QRectF(center.x() - outer_r + 3, center.y() - outer_r + 3,
                       (outer_r - 3) * 2, (outer_r - 3) * 2),
                int(start * 16),
                int(-span * 16),
            )

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#0d1117"))
        painter.drawEllipse(center, inner_r, inner_r)

        val_str = f"{self._value:.0f}%"
        painter.setPen(QColor("#e6edf3"))
        font = QFont("Tahoma", 20, QFont.Weight.Bold)
        painter.setFont(font)
        tr = painter.fontMetrics().boundingRect(val_str)
        painter.drawText(
            QPointF(center.x() - tr.width() / 2, center.y() + tr.height() / 3),
            val_str,
        )

        if self._label:
            painter.setPen(QColor("#8b949e"))
            font2 = QFont("Tahoma", 9)
            painter.setFont(font2)
            tr2 = painter.fontMetrics().boundingRect(self._label)
            painter.drawText(
                QPointF(center.x() - tr2.width() / 2, center.y() + tr.height() + 14),
                self._label,
            )


class TrendChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._series: dict[str, list[tuple[str, float]]] = {}
        self._series_colors: dict[str, QColor] = {}
        self._show_grid = True
        self._zoom = 1.0
        self._pan_offset = 0.0
        self._grid_color = QColor("#21262d")
        self._text_color = QColor("#8b949e")
        self._bg_color = QColor("#0d1117")
        self._margin_left = 50
        self._margin_right = 16
        self._margin_top = 16
        self._margin_bottom = 40
        self.setMinimumSize(300, 200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def add_series(self, name: str, data: list[tuple[str, float]], color: str = "#58a6ff"):
        self._series[name] = data
        self._series_colors[name] = QColor(color)
        self.update()

    def clear(self):
        self._series.clear()
        self._series_colors.clear()
        self.update()

    def paintEvent(self, event):
        if not self._series:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        painter.fillRect(0, 0, w, h, self._bg_color)

        plot_l = self._margin_left
        plot_r = w - self._margin_right
        plot_t = self._margin_top
        plot_b = h - self._margin_bottom
        plot_w = plot_r - plot_l
        plot_h = plot_b - plot_t

        all_values: list[float] = []
        for data in self._series.values():
            for _, val in data:
                all_values.append(val)
        if not all_values:
            return

        data_min = min(all_values)
        data_max = max(all_values)
        data_range = data_max - data_min if data_max != data_min else 1

        if self._show_grid:
            painter.setPen(QPen(self._grid_color, 1, Qt.PenStyle.DotLine))
            n_grid = 4
            for i in range(n_grid + 1):
                y = plot_t + (plot_h / n_grid) * i
                painter.drawLine(QPointF(plot_l, y), QPointF(plot_r, y))

                val = data_max - (data_range / n_grid) * i
                label = f"{val:.0f}"
                painter.setPen(self._text_color)
                font = QFont("Tahoma", 8)
                painter.setFont(font)
                tr = painter.fontMetrics().boundingRect(label)
                painter.drawText(QPointF(plot_l - tr.width() - 6, y + tr.height() / 3), label)

        for name, data in self._series.items():
            if len(data) < 2:
                continue
            color = self._series_colors.get(name, QColor("#58a6ff"))
            n = len(data)
            points: list[QPointF] = []
            for i, (_, val) in enumerate(data):
                x = plot_l + (i / (n - 1)) * plot_w
                y = plot_t + plot_h - ((val - data_min) / data_range) * plot_h
                points.append(QPointF(x, y))

            path = QPainterPath()
            path.moveTo(points[0])
            for pt in points[1:]:
                path.lineTo(pt)

            painter.setPen(QPen(color, 2))
            painter.drawPath(path)

            fill = QColor(color)
            fill.setAlpha(25)
            fill_path = QPainterPath(path)
            fill_path.lineTo(points[-1].x(), plot_b)
            fill_path.lineTo(points[0].x(), plot_b)
            fill_path.closeSubpath()
            painter.fillPath(fill_path, fill)

        painter.setPen(QPen(self._grid_color, 1))
        painter.drawLine(QPointF(plot_l, plot_t), QPointF(plot_l, plot_b))
        painter.drawLine(QPointF(plot_l, plot_b), QPointF(plot_r, plot_b))

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self._zoom *= 1.1
        else:
            self._zoom = max(0.1, self._zoom / 1.1)
        self.update()


class DataTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_data: list[list[str]] = []
        self._filtered_data: list[list[str]] = []
        self._columns: list[str] = []
        self._page = 0
        self._page_size = 50
        self._total_pages = 0

        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.verticalHeader().setVisible(False)

    def set_data(self, columns: list[str], data: list[list[str]]):
        self._columns = columns
        self._all_data = data
        self._filtered_data = list(data)
        self._page = 0
        self._refresh()

    def _refresh(self):
        self.setSortingEnabled(False)
        start = self._page * self._page_size
        end = start + self._page_size
        page_data = self._filtered_data[start:end]
        self._total_pages = max(1, math.ceil(len(self._filtered_data) / self._page_size))

        self.setColumnCount(len(self._columns))
        self.setHorizontalHeaderLabels(self._columns)
        self.setRowCount(len(page_data))

        for i, row in enumerate(page_data):
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                item.setToolTip(str(val))
                self.setItem(i, j, item)

        self.setSortingEnabled(True)

    def filter_by(self, column: int, text: str):
        if not text:
            self._filtered_data = list(self._all_data)
        else:
            self._filtered_data = [
                row for row in self._all_data
                if column < len(row) and text.lower() in str(row[column]).lower()
            ]
        self._page = 0
        self._refresh()

    def next_page(self):
        if self._page < self._total_pages - 1:
            self._page += 1
            self._refresh()

    def prev_page(self):
        if self._page > 0:
            self._page -= 1
            self._refresh()

    @property
    def page_info(self) -> str:
        return f"Page {self._page + 1} of {self._total_pages} ({len(self._filtered_data)} total)"


class StatusIndicator(QWidget):
    def __init__(self, status: str = "unknown", parent=None):
        super().__init__(parent)
        self._status = status
        self.setFixedSize(14, 14)

    def set_status(self, status: str):
        self._status = status
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color_map = {
            "active": QColor("#3fb950"),
            "completed": QColor("#3fb950"),
            "online": QColor("#3fb950"),
            "inactive": QColor("#f85149"),
            "error": QColor("#f85149"),
            "offline": QColor("#f85149"),
            "pending": QColor("#d29922"),
            "in_progress": QColor("#58a6ff"),
            "syncing": QColor("#d29922"),
            "unknown": QColor("#6e7681"),
        }
        color = color_map.get(self._status, QColor("#6e7681"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(1, 1, 12, 12)


class AlertBadge(QWidget):
    def __init__(self, count: int = 0, parent=None):
        super().__init__(parent)
        self._count = count
        self.setFixedSize(22, 22)

    def set_count(self, count: int):
        self._count = count
        self.setVisible(count > 0)
        self.update()

    def paintEvent(self, event):
        if self._count <= 0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#f85149"))
        painter.drawEllipse(0, 0, 22, 22)

        text = str(min(self._count, 99))
        painter.setPen(QColor("#ffffff"))
        font = QFont("Tahoma", 8, QFont.Weight.Bold)
        painter.setFont(font)
        tr = painter.fontMetrics().boundingRect(text)
        painter.drawText(
            QPointF(11 - tr.width() / 2, 11 + tr.height() / 3),
            text,
        )


class SearchBar(QLineEdit):
    search_triggered = Signal(str)

    def __init__(self, placeholder: str = "Search...", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setProperty("search", True)
        self.setMinimumHeight(36)
        self.setClearButtonEnabled(True)

        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(300)
        self._debounce_timer.timeout.connect(self._on_debounced)
        self.textChanged.connect(self._debounce_timer.start)

    def _on_debounced(self):
        self.search_triggered.emit(self.text())
