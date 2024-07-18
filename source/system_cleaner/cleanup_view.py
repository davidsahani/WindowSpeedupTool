from typing import Any, Callable, override

from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import (
    QFrame,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from widgets.message_bar import Message


class BorderWidget(Message):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(False, parent)

    @override
    def initializeUI(self) -> None:
        self.setupWidgets()
        self.setObjectName("BorderWidget")

    @override
    def setupWidgets(self) -> None:
        super().setupWidgets()
        self.close_button = QPushButton("✕")
        self.cancel_button = QPushButton("Cancel")

        self.close_button.setObjectName("CloseButton")
        self.close_button.hide()  # hide initially.

        size_policy = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        self.close_button.setSizePolicy(size_policy)
        self.cancel_button.setSizePolicy(size_policy)

        self.close_button.clicked.connect(
            lambda: self.showCloseButton(False)
        )
        self.cancel_button.clicked.connect(
            lambda: self.showCloseButton(True)
        )

        layout = self.layout()
        if layout is None:
            return self.setMessage(
                f"{self.__class__.__name__} LayoutError: layout is None.", True
            )

        layout.addWidget(self.close_button)
        layout.addWidget(self.cancel_button)

    def showCloseButton(self, show_close: bool) -> None:
        """Show close button if True otherwise cancel button."""
        if show_close:
            self.close_button.show()
            self.cancel_button.hide()
        else:
            self.cancel_button.show()
            self.close_button.hide()


class CleanupView(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setupWidgets()

    def setupWidgets(self) -> None:
        """Setup the widgets in layout."""
        self.text_widget = QPlainTextEdit(self)
        self.text_widget.setReadOnly(True)
        self.border_widget = BorderWidget(self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.text_widget)
        layout.addWidget(self.border_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def appendText(self, text: str) -> None:
        """Append text into text-widget and update cursor position."""
        self.text_widget.insertPlainText(text + '\n')
        # move the cursor to the end of the line.
        cursor = self.text_widget.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
        self.text_widget.setTextCursor(cursor)

    def setBorderMessage(self, message: str) -> None:
        """Set border label text message."""
        self.border_widget.setMessage(message)

    def connectClose(self, function: Callable[[], Any]) -> None:
        """Connect the function to close button press event."""
        self.border_widget.close_button.clicked.connect(function)

    def connectCancel(self, function: Callable[[], Any]) -> None:
        """Connect the function to cancel button press event."""
        self.border_widget.cancel_button.clicked.connect(function)
