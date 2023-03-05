from typing import Callable

from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import (QFrame, QPlainTextEdit, QPushButton,
                             QStackedWidget, QVBoxLayout, QWidget)

from widgets.overlay import Message


class BorderWidget(Message):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent, False)
        self.__close_function = None
        self.__cancel_function = None
        self.close_button.hide()    # hide initially

    def initializeUI(self) -> None:
        self.setupWidgets()
        self.setWidgetsSizePolicy()
        self.setObjectName("BorderWidget")

    def setupWidgets(self) -> None:
        super().setupWidgets()
        self.close_button = QPushButton("✕")
        self.cancel_button = QPushButton("Cancel")
        self.close_button.setObjectName("CloseButton")
        self.close_button.clicked.connect(self.onClose)  # type:ignore
        self.cancel_button.clicked.connect(self.onCancel)  # type:ignore
        self.layout().addWidget(self.close_button)
        self.layout().addWidget(self.cancel_button)

    def setVisibleCloseButton(self, visible: bool) -> None:
        """show/hide close button"""
        if visible:
            self.close_button.show()
            self.cancel_button.hide()
        else:
            self.cancel_button.show()
            self.close_button.hide()

    def connectClose(self, function: Callable[[], None]) -> None:
        """Connect the function to close button press event"""
        self.__close_function = function

    def connectCancel(self, function: Callable[[], None]) -> None:
        """Connect the function to Cancel button press event"""
        self.__cancel_function = function

    def onClose(self) -> None:
        """Handle the cancel button press event"""
        function = self.__close_function
        if function is not None:
            function()

    def onCancel(self) -> None:
        """Handle the cancel button press event"""
        function = self.__cancel_function
        if function is not None:
            function()


class CleanupView(QFrame):
    def __init__(self, master: QWidget, parent: QStackedWidget) -> None:
        super().__init__(parent)
        self._master = master
        self._parent = parent
        self.setupWidgets()
        self.addSelf()

    def addSelf(self) -> None:
        """Add self to stacked widget"""
        self.__initial = True
        self._parent.addWidget(self)
        self._parent.setCurrentWidget(self)
        self._parent.currentChanged.connect(self.switchToSelf)  # type: ignore

    def switchToSelf(self) -> None:
        """Switch current stacked widget to self.

        if it's master widget to show result
        """
        if not self._parent.currentWidget() is self._master:
            return
        if self.__initial:
            self.__initial = False
            return
        self._parent.setCurrentWidget(self)

    def switchToMaster(self) -> None:
        """Switch to master widget"""
        self._parent.setCurrentWidget(self._master)
        self._parent.removeWidget(self)
        self.deleteLater()  # delete this widget when changed

    def setupWidgets(self) -> None:
        """Setup widgets in layout"""
        self.text_widget = QPlainTextEdit()
        self.border_widget = BorderWidget(self)
        self.border_widget.connectClose(self.switchToMaster)

        layout = QVBoxLayout(self)
        layout.addWidget(self.text_widget)
        layout.addWidget(self.border_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def appendText(self, text: str) -> None:
        """Append text into text-widget and update cursor position"""
        self.text_widget.insertPlainText(text + '\n')
        # move the cursor to the end of the line
        cursor = self.text_widget.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
        self.text_widget.setTextCursor(cursor)

    def setText(self, text: str) -> None:
        """Set border label text"""
        self.border_widget.displayMessage(text)

    def setMessage(self, message: str) -> None:
        """Set final text message"""
        self.border_widget.displayMessage(message)
        self.text_widget.setReadOnly(True)
        self.border_widget.setVisibleCloseButton(True)

    def connectCancel(self, function: Callable[[], None]) -> None:
        """Connect the function to cancel button press event"""
        self.border_widget.connectCancel(function)
