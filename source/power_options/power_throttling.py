import os
import re
from typing import override

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from utils import power
from widgets.message_bar import MessageBar


class PowerThrottling(QFrame):
    def __init__(self, message_bar: MessageBar, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.message_bar = message_bar
        self._app_buttons: dict[str, tuple[QPushButton, QPushButton]] = {}
        self.setupWidgets()

    def setupWidgets(self) -> None:
        """Setup widgets in layout."""
        layout = QVBoxLayout()
        layout.addWidget(self.createApplicationsGroupBox())
        layout.setSpacing(1)
        layout.addWidget(self.createAddApplicationWidget())
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def createApplicationsGroupBox(self) -> QGroupBox:
        """Create group box for power-throttling applications."""
        self.apps_grid = QGridLayout()

        result = power.list_powerthrottling()
        if result.value is None:
            self.message_bar.displayMessage(result.error.stderr, True)

        for row, application in enumerate(result.value or []):
            self.insertApplicationButtons(application, row)

        group_box = QGroupBox()
        group_box.setTitle("Power Throttling Disabled Apps")
        group_box.setLayout(self.apps_grid)
        return group_box

    def insertApplicationButtons(self, application: str, row: int) -> None:
        """Insert application add and remove buttons to the layout."""
        application_button = QPushButton(application)
        application_button.setObjectName("ApplicationButton")

        remove_button = QPushButton("✕")
        remove_button.setObjectName("RemoveButton")
        remove_button.clicked.connect(
            lambda: self.removeApplication(application)
        )

        self.apps_grid.addWidget(application_button, row, 0)
        self.apps_grid.addWidget(
            remove_button, row, 1, Qt.AlignmentFlag.AlignRight
        )
        self._app_buttons[application] = application_button, remove_button

    def createAddApplicationWidget(self) -> QWidget:
        """Create widget for adding application."""
        self.line_edit = QLineEdit()
        self.line_edit.setMinimumWidth(300)
        self.line_edit.setPlaceholderText("Enter application name or path")

        file_button = QPushButton("Browse...")
        add_button = QPushButton("┿")
        add_button.setObjectName("AddButton")
        add_button.setToolTip("Add application")

        file_button.clicked.connect(self.openFile)
        add_button.clicked.connect(self.addApplication)

        self.warning_label = QLabel()
        self.warning_label.setObjectName("WarningLabel")

        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.addWidget(self.line_edit)
        layout.addWidget(file_button)
        layout.addWidget(add_button)
        layout.addWidget(self.warning_label)
        layout.setStretchFactor(self.warning_label, 1)
        layout.setContentsMargins(0, 6, 0, 0)
        widget.setLayout(layout)
        return widget

    def openFile(self) -> None:
        """Open application file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open Application", "", "Applications (*.exe)"
        )
        if filepath:
            self.line_edit.setText(filepath)

    @override
    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        """Add application on Enter key press."""
        if not self.line_edit.hasFocus() or a0 is None:
            return
        if self.warning_label.text():
            self.warning_label.setText("")
        if a0.key() in (Qt.Key.Key_Return,
                        Qt.Key.Key_Enter):
            self.addApplication()

    def addApplication(self) -> None:
        """Add application to apps' group-box and disable power throttling."""
        text = self.line_edit.text()
        if not text:
            return  # no input.
        if text in self._app_buttons:
            return  # already added.

        if self.ispath(text):
            if not os.path.splitext(text)[1] or text.endswith('.'):
                self.warning_label.setText("Invalid application filepath")
                return
            if not text.endswith('.exe'):
                self.warning_label.setText("Invalid executable")
                return
            if not os.path.isfile(text):
                self.warning_label.setText("File doesn't exist")
                return
        elif not self.is_application(text):
            self.warning_label.setText("Invalid application name")
            return

        self.warning_label.setText("")

        result = power.disable_powerthrottling(text)
        if result.status != 0:
            return self.message_bar.displayMessage(result.error, True)

        self.line_edit.clear()
        self.insertApplicationButtons(text, self.apps_grid.rowCount())
        self.update()  # update the window.

    def removeApplication(self, application: str) -> None:
        """Remove application from apps' group-box and reset power throttling."""
        result = power.reset_powerthrottling(application)
        if result.status != 0:
            return self.message_bar.displayMessage(result.error, True)

        buttons = self._app_buttons.pop(application, None)
        if buttons is None:
            return self.message_bar.displayMessage(
                "InternalError: Failed to remove application entry.", True
            )
        add_button, remove_button = buttons
        self.apps_grid.removeWidget(add_button)
        self.apps_grid.removeWidget(remove_button)
        self.update()  # update the window.

    @staticmethod
    def is_application(name: str) -> bool:
        """Check if executable name is valid."""
        return re.match(r'([\w-])*\.exe$', name) is not None

    @staticmethod
    def ispath(filepath: str) -> bool:
        """Check if filepath is valid windows path."""
        pattern1 = r'^[a-zA-Z]:/(?:[^//:*?"<>|\r\n]+/)*[^//:*?"<>|\r\n]*$'
        pattern2 = r'^[a-zA-Z]:\\(?:[^\\/:*?"<>|\r\n]+\\)*[^\\/:*?"<>|\r\n]*$'
        return bool(re.match(pattern1, filepath) or re.match(pattern2, filepath))
