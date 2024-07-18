from typing import override

from PyQt6.QtCore import QEvent, QObject, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QLabel, QWidget


class ShowEventFilter(QObject):
    def __init__(self, widget: QWidget, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._widget = widget

    @override
    def eventFilter(self, a0: QObject | None, a1: QEvent | None) -> bool:
        if a0 is None or a1 is None:
            return False
        event_type = a1.type()
        if event_type == QEvent.Type.Show:
            self._widget.show()
        elif event_type == QEvent.Type.Hide:
            self._widget.hide()
        return super().eventFilter(a0, a1)


class SizeGrip(QLabel):
    def __init__(self, resize_widget: QWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.min_height = 150
        self._resizing = False
        self._resize_widget = resize_widget

        self.setText("―")
        self.setFixedHeight(8)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.SizeVerCursor)

        self._curr_height = self._resize_widget.height()
        self._event_filter = ShowEventFilter(self)
        resize_widget.installEventFilter(self._event_filter)

    @override
    def mousePressEvent(self, ev: QMouseEvent | None) -> None:
        super().mousePressEvent(ev)
        if ev is None:
            return
        self._resizing = True
        self._curr_height = self._resize_widget.height()
        self.mouse_press_pos = ev.globalPosition()

    @override
    def mouseMoveEvent(self, ev: QMouseEvent | None) -> None:
        super().mouseMoveEvent(ev)
        if not self._resizing or ev is None:
            return
        height_diff = self.mouse_press_pos.y() - ev.globalPosition().y()
        height = self._curr_height + int(height_diff)
        if height > self.min_height:
            self._resize_widget.setFixedHeight(height)

    @override
    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        super().mouseReleaseEvent(ev)
        self._resizing = False
