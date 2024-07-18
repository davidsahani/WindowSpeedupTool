from typing import override

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QFrame, QScrollArea, QWidget


class SwipableScrollArea(QScrollArea):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)

        scroll_bar_policy = Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        self.setVerticalScrollBarPolicy(scroll_bar_policy)
        self.setHorizontalScrollBarPolicy(scroll_bar_policy)

        self.__start_pos = None
        self.__scrolling = False

    @override
    def minimumSizeHint(self) -> QSize:
        size_hint = super().minimumSizeHint()
        return QSize(size_hint.width(), 0)

    @override
    def mousePressEvent(self, a0: QMouseEvent | None) -> None:
        if a0 and a0.button() == Qt.MouseButton.LeftButton:
            self.__start_pos = a0.position()
            self.__scrolling = True
        super().mousePressEvent(a0)

    @override
    def mouseMoveEvent(self, a0: QMouseEvent | None) -> None:
        if a0 and self.__scrolling and self.__start_pos is not None:
            delta = a0.position() - self.__start_pos
            horizontal_scroll_bar = self.horizontalScrollBar()
            if horizontal_scroll_bar:
                horizontal_scroll_bar.setValue(
                    horizontal_scroll_bar.value() - int(delta.x())
                )
            vertical_scroll_bar = self.verticalScrollBar()
            if vertical_scroll_bar:
                vertical_scroll_bar.setValue(
                    vertical_scroll_bar.value() - int(delta.y())
                )
            self.__start_pos = a0.position()
        super().mouseMoveEvent(a0)

    @override
    def mouseReleaseEvent(self, a0: QMouseEvent | None) -> None:
        if a0 and a0.button() == Qt.MouseButton.LeftButton:
            self.__scrolling = False
        super().mouseReleaseEvent(a0)
