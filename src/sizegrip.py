from PyQt6.QtCore import QEvent, QObject, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QLabel, QWidget


class ShowEventFilter(QObject):
    def __init__(self, widget: QWidget) -> None:
        super().__init__()
        self.widget = widget

    def eventFilter(self, a0: QObject, a1: QEvent) -> bool:
        event_type = a1.type()
        if event_type == QEvent.Type.Show:
            self.widget.show()
        elif event_type == QEvent.Type.Hide:
            self.widget.hide()
        return super().eventFilter(a0, a1)


class SizeGrip(QLabel):
    def __init__(self, parent: QWidget, resize_widget: QWidget) -> None:
        super().__init__(parent)
        self.resize_widget = resize_widget
        self.min_height = 150
        self.setText("―")
        self.setFixedHeight(7)
        self.resizing = False
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.SizeVerCursor)
        self.curr_height = self.resize_widget.height()

        self.event_filter = ShowEventFilter(self)
        resize_widget.installEventFilter(self.event_filter)

    def mousePressEvent(self, ev: QMouseEvent) -> None:
        super().mousePressEvent(ev)
        self.resizing = True
        self.curr_height = self.resize_widget.height()
        self.mouse_press_pos = ev.globalPosition()

    def mouseMoveEvent(self, ev: QMouseEvent) -> None:
        super().mouseMoveEvent(ev)
        if not self.resizing:
            return
        height_diff = self.mouse_press_pos.y() - ev.globalPosition().y()
        height = self.curr_height + int(height_diff)
        if height > self.min_height:
            self.resize_widget.setFixedHeight(height)

    def mouseReleaseEvent(self, ev: QMouseEvent) -> None:
        super().mouseReleaseEvent(ev)
        self.resizing = False

    def reposition(self):
        rect = self.resize_widget.geometry()
        self.move(rect.right(), rect.bottom())
