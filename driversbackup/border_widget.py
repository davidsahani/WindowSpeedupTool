from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QFileDialog, QHBoxLayout, QLabel, QProgressBar,
                             QPushButton, QSizePolicy, QStackedWidget,
                             QVBoxLayout, QWidget)

from src.overlay import MessageOverlay


class ActionWidget(QWidget):
    def __init__(self, parent: QWidget, backup_dir: str) -> None:
        super().__init__(parent)
        self.backup_dir = backup_dir
        self.__function = None
        self.setupWidgets()
        self.setObjectName("ActionWidget")

    def setupWidgets(self) -> None:
        """Setup the widgets in layout"""
        self.label = QLabel(f"Backup dir: {self.backup_dir}")
        self.browse_button = QPushButton("Select backup dir")
        self.backup_button = QPushButton("Backup selected drivers")
        self.browse_button.clicked.connect(self.onBrowseDir)  # type: ignore
        self.backup_button.clicked.connect(self.onBackupPress)  # type: ignore

        layout = QHBoxLayout()
        layout.addWidget(self.label, 1)
        layout.addWidget(self.browse_button, 0)
        layout.addWidget(self.backup_button, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeading)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def onBrowseDir(self) -> None:
        """Browse/set backup dir"""
        dir = QFileDialog.getExistingDirectory(
            self, "Select backup directory", "",
        )
        if not dir:
            return  # if no dir selected
        self.backup_dir = dir
        self.label.setText(f"Backup dir: {dir}")

    def onBackupPress(self) -> None:
        """Handle backup button press event"""
        function = self.__function
        if function is not None:
            function()

    def connect(self, function: Callable[[], None]) -> None:
        """Connect the function to backup button press event"""
        self.__function = function


class BorderWidget(QWidget):
    def __init__(self, parent: QWidget, backup_dir: str) -> None:
        super().__init__(parent)
        self._backup_dir = backup_dir
        self.setupWidgets()

    def setupWidgets(self) -> None:
        """Setup the widgets in layout"""
        self.action_widget = ActionWidget(self, self._backup_dir)
        self.progressbar = QProgressBar(self)
        self.message_overlay = MessageOverlay(self, False)
        self.widget_heights = {
            0: 35,
            1: 35,
            2: 45
        }
        stacked_widget = QStackedWidget(self)
        self.stacked_widget = stacked_widget
        stacked_widget.currentChanged.connect(  # type: ignore
            self.onWidgetChange)
        stacked_widget.addWidget(self.action_widget)
        stacked_widget.addWidget(self.progressbar)
        stacked_widget.addWidget(self.message_overlay)
        stacked_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        self.message_overlay.connect(self.switchToMain)
        self.message_overlay.connectClose(self.switchToMain)
        self.message_overlay.connectCancel(self.switchToMain)
        self.message_overlay.setConfirmText("Show")

        layout = QVBoxLayout(self)
        layout.addWidget(stacked_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    @property
    def backup_dir(self) -> str:
        return self.action_widget.backup_dir

    def switchToMain(self) -> None:
        """Switch to action widget"""
        self.stacked_widget.setCurrentWidget(self.action_widget)

    def onWidgetChange(self, index: int) -> None:
        """Adjust stacked widget height on widget change"""
        height = self.widget_heights[index]
        self.stacked_widget.setFixedHeight(height)

    def showProgressBar(self) -> None:
        """Switch to progress bar widget"""
        self.stacked_widget.setCurrentWidget(self.progressbar)

    def connectBackup(self, function: Callable[[], None]) -> None:
        """Connect the function to backup button press event"""
        self.action_widget.connect(function)

    def displayMessage(self, message: str, is_warning: bool = False) -> None:
        """Display the message overlay with close button.

        display message in warning style if `is_warning` is set to True.
        """
        self.message_overlay.displayMessage(message, is_warning)
        self.stacked_widget.setCurrentWidget(self.message_overlay)

    def displayPrompt(self, message: str, is_warning: bool = False) -> None:
        """Display the message prompt overlay.

        display message in warning style if `is_warning` is set to True.
        """
        self.message_overlay.displayPrompt(message, is_warning)
        self.stacked_widget.setCurrentWidget(self.message_overlay)
