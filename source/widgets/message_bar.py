from typing import Callable, Concatenate, override, ParamSpec, TypeVar

from PyQt6.QtCore import pyqtSignal, QEvent, Qt, QTime, QTimer
from PyQt6.QtGui import QEnterEvent
from PyQt6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QWidget,
)

from utils import styles

from .swipable_scroll_area import SwipableScrollArea

P = ParamSpec('P')
R = TypeVar('R')


class Message(QWidget):
    timeout = pyqtSignal()

    def __init__(self, enable_timer: bool, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.enable_timer = enable_timer
        self.timeout_in_secs = 10

        self._time = QTime(0, 0, 0)
        self._timer = QTimer()
        self._timer.timeout.connect(self.handleTimerTick)

        self._is_warning_color_set = False
        self.initializeUI()  # initialize ui and setup widgets
        self.default_color = self.label.palette().text().color().name()

    def initializeUI(self) -> None:
        self.setupWidgets()
        self.setStyleSheet(styles.get("message_bar"))
        assert hasattr(self, "label")  # label must be created by subclass

    def setupWidgets(self) -> None:
        self.label = QLabel()
        self.label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout = QHBoxLayout()
        layout.addWidget(self.label, stretch=1)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeading)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def setMessage(self, message: str, is_warning: bool = False) -> None:
        """Set label text and text color, and restart the timer."""
        self.label.setText(message)
        self.setTextColor(is_warning)
        self.stopTimer()
        self.initiateTimer()

    def setTextColor(self, is_warning: bool) -> None:
        """Set label warning text color"""
        if is_warning and self._is_warning_color_set:
            return  # already warning color set.
        if not is_warning and not self._is_warning_color_set:
            return  # it's default color.

        if is_warning:
            self._is_warning_color_set = True
            self.label.setStyleSheet("QLabel {color: Coral};")
        else:
            self._is_warning_color_set = False
            self.label.setStyleSheet(
                "QLabel {color: %s};" % self.default_color
            )

    @override
    def enterEvent(self, event: QEnterEvent | None) -> None:
        """Stop the timer on mouse enter event."""
        self._timer.stop()
        super().enterEvent(event)

    @override
    def leaveEvent(self, a0: QEvent | None) -> None:
        """Start the timer on mouse enter leave."""
        self.initiateTimer()
        super().leaveEvent(a0)

    def initiateTimer(self) -> None:
        """Start the timer"""
        if not self.enable_timer:
            return  # don't start timer.
        self._time.setHMS(0, 0, 0)
        self._timer.start(1000)  # tick every 1 second.

    def handleTimerTick(self) -> None:
        """Increment time, stop timer and emit timeout."""
        second = self._time.second()
        if second < self.timeout_in_secs:
            self._time.setHMS(0, 0, second + 1)
        else:
            self.stopTimer()
            self.timeout.emit()

    def stopTimer(self) -> None:
        """Stop timer and reset time."""
        self._timer.stop()
        self._time.setHMS(0, 0, 0)


class MessageClose(Message):
    @override
    def setupWidgets(self) -> None:
        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setMinimumHeight(30)

        self.close_button = QPushButton("✕")
        self.close_button.setObjectName("CloseButton")
        self.close_button.setFixedHeight(36)

        self.scroll_area = SwipableScrollArea()
        self.scroll_area.setWidget(self.label)

        size_policy = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self.label.setSizePolicy(size_policy)
        self.scroll_area.setSizePolicy(size_policy)

        layout = QGridLayout()
        layout.addWidget(self.scroll_area, 0, 0)
        layout.addWidget(
            self.close_button, 0, 0,
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight
        )
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    @override
    def setMessage(self, message: str, is_warning: bool = False) -> None:
        super().setMessage(message, is_warning)
        if len(message.rsplit('\n', maxsplit=2)) == 1 and \
                self.label.fontMetrics().\
                boundingRect(self.label.text()).\
                width() < self.label.width():
            self.scroll_area.setFixedHeight(36)
        else:
            self.scroll_area.setFixedHeight(
                max(min(self.label.sizeHint().height() + 5, 160), 36)
            )
        v_scroll_bar = self.scroll_area.verticalScrollBar()
        _ = v_scroll_bar and v_scroll_bar.setValue(0)  # scroll to top.


class MessagePrompt(Message):
    def __init__(self, enable_timer: bool, parent: QWidget | None = None) -> None:
        super().__init__(enable_timer, parent)
        self.timeout_in_secs = 25

    @override
    def setupWidgets(self) -> None:
        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setMinimumHeight(35)

        self.cancel_button = QPushButton("Cancel")
        self.confirm_button = QPushButton("Confirm")

        self.label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        size_policy = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self.confirm_button.setSizePolicy(size_policy)
        self.cancel_button.setSizePolicy(size_policy)

        layout = QGridLayout()
        layout.addWidget(self.label, 0, 0)
        layout.addWidget(self.cancel_button, 0, 1)
        layout.addWidget(self.confirm_button, 0, 2)
        layout.setColumnStretch(0, 1)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)


class MessageBar(QWidget):
    def __init__(self, enable_timer: bool = True, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.enable_timer = enable_timer

        self.__close_func_args = None
        self.__confirm_func_args = None
        self.__cancel_func_args = None

        self.setupWidgets()
        self.message_prompt.hide()
        self.hide()  # start the widget hidden.

    def setupWidgets(self) -> None:
        self.message_close = MessageClose(self.enable_timer)
        self.message_prompt = MessagePrompt(self.enable_timer)

        self.message_close.close_button.clicked.connect(self.onClose)
        self.message_prompt.confirm_button.clicked.connect(self.onConfirm)
        self.message_prompt.cancel_button.clicked.connect(self.onCancel)

        # connect timeout action to hide the widget.
        self.message_close.timeout.connect(self.hide)
        self.message_prompt.timeout.connect(self.hide)

        layout = QGridLayout(self)
        layout.addWidget(self.message_close, 0, 0)
        layout.addWidget(self.message_prompt, 0, 0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def setConfirmText(self, text: str) -> None:
        """Set text of the confirm button."""
        self.message_prompt.confirm_button.setText(text)

    def setCancelText(self, text: str) -> None:
        """Set text of the cancel button."""
        self.message_prompt.cancel_button.setText(text)

    def setRetryStyleForCloseButton(self, value: bool) -> None:
        """Set the close button's text and object name.

        If `value` is True, set to "Retry"; otherwise, set to "✕".
        """
        if value:
            self.message_close.close_button.setText("Retry")
            self.message_close.close_button.setObjectName("RetryButton")
            self.message_close.enable_timer = False
        else:
            self.message_close.close_button.setText("✕")
            self.message_close.close_button.setObjectName("CloseButton")
            self.message_close.enable_timer = True

    def displayMessage(self, message: str, is_warning: bool = False) -> None:
        """Display the message bar with close button.

        display message in warning style if `is_warning` is True.
        """
        self.message_prompt.stopTimer()
        self.message_close.setMessage(message, is_warning)
        self._showMessageClose(True)  # show message-close

    def displayPrompt(self, message: str, is_warning: bool = False) -> None:
        """Display the message bar with confirm and cancel buttons.

        display message in warning style if `is_warning` is True.
        """
        self.message_close.stopTimer()
        self.message_prompt.setMessage(message, is_warning)
        self._showMessageClose(False)  # show message-prompt

    def _showMessageClose(self, show: bool) -> None:
        """Show MessageClose if True otherwise MessagePrompt."""
        if show:
            self.message_prompt.hide()
            self.message_close.show()
        else:
            self.message_close.hide()
            self.message_prompt.show()
        self.show()  # show message-bar, it's hidden from the view

    def connect(self, function: Callable[Concatenate[P], R], *args: P.args, **kwargs: P.kwargs) -> None:
        """Connect the function to confirm button press event."""
        self.__confirm_func_args = function, args, kwargs

    def connectCancel(self, function: Callable[Concatenate[P], R], *args: P.args, **kwargs: P.kwargs) -> None:
        """Connect the function to cancel button press event."""
        self.__cancel_func_args = function, args, kwargs

    def connectClose(self, function: Callable[Concatenate[P], R], *args: P.args, **kwargs: P.kwargs) -> None:
        """Connect the function to close button press event."""
        self.__close_func_args = function, args, kwargs

    def onConfirm(self) -> None:
        """Handle the confirm button press event."""
        self.hide()  # hide message-bar.
        self.message_prompt.stopTimer()
        func_args = self.__confirm_func_args
        if func_args is not None:
            func, args, kwargs = func_args
            func(*args, **kwargs)

    def onCancel(self) -> None:
        """Handle the cancel button press event."""
        self.hide()  # hide message-bar.
        self.message_prompt.stopTimer()
        func_args = self.__cancel_func_args
        if func_args is not None:
            func, args, kwargs = func_args
            func(*args, **kwargs)

    def onClose(self) -> None:
        """Handle the close button press event."""
        self.hide()  # hide message-bar.
        self.message_close.stopTimer()
        func_args = self.__close_func_args
        if func_args is not None:
            func, args, kwargs = func_args
            func(*args, **kwargs)
