from typing import Any, Callable

from PyQt6.QtCore import QEvent, Qt, QTime, QTimer
from PyQt6.QtGui import QEnterEvent
from PyQt6.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QSizePolicy,
                             QStackedWidget, QVBoxLayout, QWidget)

import styles


class Message(QWidget):
    def __init__(self, parent: QWidget | None = None, enable_timeout: bool = True) -> None:
        super().__init__(parent)
        self.enable_timeout = enable_timeout
        self.timer = QTimer()
        self.timeout_in_secs = 10
        self.initializeUI()
        self._is_warning_color_set = False
        self.default_color = self.label.palette().button().color().name()

    def initializeUI(self) -> None:
        self.setupWidgets()
        self.setWidgetsSizePolicy()
        self.setStyleSheet(styles.get("overlay"))

    def setupWidgets(self) -> None:
        self.label = QLabel()
        layout = QHBoxLayout(self)
        layout.addWidget(self.label)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeading)
        layout.setStretchFactor(self.label, 1)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def setWidgetsSizePolicy(self) -> None:
        layout = self.layout()
        for idx in range(layout.count()):
            widget = layout.itemAt(idx).widget()
            widget.setSizePolicy(  # set widgets size policy expanding
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def setTextWarning(self, is_warning: bool = False) -> None:
        """Set label warning text color"""
        if is_warning and self._is_warning_color_set:
            return  # already warning color set
        if not is_warning and not self._is_warning_color_set:
            return  # it's default color

        if is_warning:
            self._is_warning_color_set = True
            self.label.setStyleSheet("QLabel {color: Coral};")
        else:
            self._is_warning_color_set = False
            self.label.setStyleSheet(
                "QLabel {color: %s};" % self.default_color)

    def displayMessage(self, message: str, is_warning: bool = False) -> None:
        """Set label text and style, and start the timer"""
        self.setTextWarning(is_warning)
        self.label.setText(message)
        self.initiateTimer()

    def enterEvent(self, event: QEnterEvent) -> None:
        """Stop the timer on mouse enter event"""
        self.timer.stop()

    def leaveEvent(self, a0: QEvent) -> None:
        """Start the timer on mouse enter leave"""
        self.initiateTimer()

    def initiateTimer(self) -> None:
        """Start the timer"""
        if not self.enable_timeout:
            return  # don't start timer
        self.time = QTime(0, 0, 0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.timerHandler)   # type:ignore
        self.timer.start(1000)

    def timerHandler(self) -> None:
        """increment time, stop timer and perform action upon reaching timeout"""
        self.time = self.time.addSecs(1)
        secs = int(self.time.toString("ss"))
        if secs < self.timeout_in_secs:
            return
        self.stopTimer()
        self.action()

    def stopTimer(self) -> None:
        """Stop the timer and reset the counter"""
        self.timer.stop()
        self.time = QTime(0, 0, 0)

    def action(self) -> None:
        """Implement a timeout action for this method."""
        raise NotImplementedError("timeout action not implemented")


class MessageClose(Message):
    def __init__(self, parent: QWidget | None = None, enable_timeout: bool = True) -> None:
        super().__init__(parent, enable_timeout)
        self.__function = None

    def setupWidgets(self) -> None:
        super().setupWidgets()
        self.close_button = QPushButton("✕")
        self.close_button.setObjectName("CloseButton")
        self.layout().addWidget(self.close_button)

    def action(self) -> None:
        """Run the connected function on timeout"""
        function = self.__function
        if function is not None:
            function()

    def connectTimeout(self, function: Callable[[], None]) -> None:
        """Connect the function to timeout event"""
        self.__function = function


class MessagePrompt(Message):
    def __init__(self, parent: QWidget | None = None, enable_timeout: bool = True) -> None:
        super().__init__(parent, enable_timeout)
        self.timeout_in_secs = 25
        self.__function = None

    def setupWidgets(self) -> None:
        super().setupWidgets()
        self.cancel_button = QPushButton("Cancel")
        self.confirm_button = QPushButton("Save Changes")
        self.layout().addWidget(self.cancel_button)
        self.layout().addWidget(self.confirm_button)

    def setConfirmText(self, text: str) -> None:
        """Set the text of the confirm button"""
        self.confirm_button.setText(text)

    def setCancelText(self, text: str) -> None:
        """Set the text of the cancel button"""
        self.cancel_button.setText(text)

    def action(self) -> None:
        """Run the connected function on timeout"""
        function = self.__function
        if function is not None:
            function()

    def connectTimeout(self, function: Callable[[], None]) -> None:
        """Connect the function to timeout event"""
        self.__function = function


class MessageOverlay(QWidget):
    def __init__(self, parent: QWidget | None = None, enable_timeout: bool = True) -> None:
        super().__init__(parent)
        self.enable_timeout = enable_timeout
        self.makeWidgets()
        self.hide()  # start hidden
        self.__close_function = None
        self.__confirm_function = None
        self.__cancel_function = None

    def makeWidgets(self) -> None:
        self.stacked_widget = QStackedWidget(self)
        self.message_close = MessageClose(self, self.enable_timeout)
        self.message_prompt = MessagePrompt(self, self.enable_timeout)
        self.stacked_widget.addWidget(self.message_close)
        self.stacked_widget.addWidget(self.message_prompt)
        # connect timeout action to hide the widget
        self.message_close.connectTimeout(self.hide)
        self.message_prompt.connectTimeout(self.hide)

        # connect close/confirm/cancel actions
        self.message_close.close_button.clicked\
            .connect(self.onClose)  # type: ignore
        self.message_prompt.confirm_button.clicked.\
            connect(self.onConfirm)  # type: ignore
        self.message_prompt.cancel_button.clicked.\
            connect(self.onCancel)  # type: ignore

        layout = QVBoxLayout(self)
        layout.addWidget(self.stacked_widget)
        layout.setAlignment(self.stacked_widget, Qt.AlignmentFlag.AlignBottom)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def setConfirmText(self, text: str) -> None:
        """Set the text of the confirm button"""
        self.message_prompt.setConfirmText(text)

    def setCancelText(self, text: str) -> None:
        """Set the text of the cancel button"""
        self.message_prompt.setCancelText(text)

    def displayMessage(self, message: str, is_warning: bool = False) -> None:
        """Display the message overlay with close button.

        display message in warning style if `is_warning` is set to True.
        """
        self.message_prompt.stopTimer()
        self.message_close.displayMessage(message, is_warning)
        self.stacked_widget.setCurrentWidget(self.message_close)
        if self.isHidden():
            self.show()

    def displayPrompt(self, message: str, is_warning: bool = False) -> None:
        """Display the message prompt overlay.

        display message in warning style if `is_warning` is set to True.
        """
        self.message_close.stopTimer()
        self.message_prompt.displayMessage(message, is_warning)
        self.stacked_widget.setCurrentWidget(self.message_prompt)
        if self.isHidden():
            self.show()

    def connect(self, function: Callable[..., Any], *args: Any) -> None:
        """Connect the function to confirm button press event"""
        self.__confirm_function = function, args

    def connectCancel(self, function: Callable[..., Any], *args: Any) -> None:
        """Connect the function to cancel button press event"""
        self.__cancel_function = function, args

    def connectClose(self, function: Callable[..., Any], *args: Any) -> None:
        """Connect the function to close button press event"""
        self.__close_function = function, args

    def onConfirm(self) -> None:
        """Handle the confirm button press event"""
        function = self.__confirm_function
        if function is not None:
            func, args = function
            func(*args)
        self.hide()

    def onCancel(self) -> None:
        """Handle the cancel button press event"""
        function = self.__cancel_function
        if function is not None:
            func, args = function
            func(*args)
        self.hide()

    def onClose(self) -> None:
        """Handle the close button press event"""
        function = self.__close_function
        if function is not None:
            func, args = function
            func(*args)
        self.hide()
