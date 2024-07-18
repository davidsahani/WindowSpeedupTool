from collections import deque
from typing import override

from PyQt6.QtWidgets import QStackedWidget, QWidget


class StackedWidget(QStackedWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._widget_indexes: deque[int] = deque(maxlen=2)
        self._disposable_widgets: list[QWidget] = []
        self.currentChanged.connect(lambda: (
            self._disposeWidgets(),
            self._widget_indexes.append(self.currentIndex())
        ))

    @override
    def addWidget(self, w: QWidget | None, dispose: bool = False) -> int:
        if dispose and w is not None:
            self._disposable_widgets.append(w)
        return super().addWidget(w)

    @override
    def removeWidget(self, w: QWidget | None) -> None:
        idx = self.indexOf(w)
        if idx in self._widget_indexes:
            self._widget_indexes.remove(idx)
        if w in self._disposable_widgets:
            self._disposable_widgets.remove(w)
        return super().removeWidget(w)

    def switchToPreviousWidget(self) -> None:
        if self._widget_indexes:
            self.setCurrentIndex(self._widget_indexes[0])

    def widgetName(self, name: str) -> QWidget | None:
        for idx in range(self.count()):
            widget = self.widget(idx)
            if widget is None:
                continue
            if widget.__class__.__name__ == name:
                return widget

    def _disposeWidgets(self) -> None:
        if not self._disposable_widgets:
            return  # on empty.

        current_widget = self.currentWidget()

        for widget in self._disposable_widgets:
            if widget is current_widget:
                continue  # don't dispose.

            self.removeWidget(widget)
            widget.deleteLater()  # delete widget later
