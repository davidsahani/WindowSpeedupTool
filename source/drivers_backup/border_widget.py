from typing import Callable, override

from PyQt6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from widgets.message_bar import MessageBar, MessagePrompt


class CustomMessagePrompt(MessagePrompt):
    @override
    def initializeUI(self) -> None:
        self.setupWidgets()
        self.setObjectName("ActionWidget")


class BorderWidget(QWidget):
    def __init__(self, parent: QWidget, backup_dir: str) -> None:
        super().__init__(parent)
        self.backup_dir = backup_dir
        self.__function = lambda: None
        self.setupWidgets()

    def setupWidgets(self) -> None:
        """Setup the widgets in layout."""
        self.stacked_widget = QStackedWidget(self)
        self.stacked_widget.setFixedHeight(43)

        self.action_widget = CustomMessagePrompt(False)
        self.message_bar = MessageBar(False)

        self.progressbar = QProgressBar()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("ProgressCancelButton")

        self.progressbar_widget = QWidget()
        progress_bar_layout = QGridLayout()
        progress_bar_layout.addWidget(self.progressbar, 0, 0)
        progress_bar_layout.addWidget(self.cancel_button, 0, 1)
        progress_bar_layout.setContentsMargins(0, 0, 0, 0)
        self.progressbar_widget.setLayout(progress_bar_layout)

        self.action_widget.label.setText(f"Backup dir: {self.backup_dir}")
        self.action_widget.cancel_button.setText("Select backup dir")
        self.action_widget.confirm_button.setText("Backup selected drivers")
        self.action_widget.cancel_button.clicked.connect(self.onBrowseDir)
        self.action_widget.confirm_button.clicked.connect(lambda: self.__function())  # noqa

        self.message_bar.setConfirmText("Show")
        self.message_bar.connectClose(self.showMainWidget)
        self.message_bar.connectCancel(self.showMainWidget)

        self.stacked_widget.addWidget(self.action_widget)
        self.stacked_widget.addWidget(self.progressbar_widget)
        self.stacked_widget.addWidget(self.message_bar)
        self.stacked_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        layout = QVBoxLayout(self)
        layout.addWidget(self.stacked_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def showMainWidget(self) -> None:
        """Switch to main action widget."""
        self.stacked_widget.setCurrentWidget(self.action_widget)

    def showProgressBar(self) -> None:
        """Switch to progress bar widget."""
        self.stacked_widget.setCurrentWidget(self.progressbar_widget)

    def connectBackup(self, function: Callable[[], None]) -> None:
        """Connect the function to backup button press event."""
        self.__function = function

    def displayMessage(self, message: str, is_warning: bool = False) -> None:
        """Display the message bar with close button.

        display message in warning style if `is_warning` is set to True.
        """
        self.message_bar.displayMessage(message, is_warning)
        self.stacked_widget.setCurrentWidget(self.message_bar)

    def displayPrompt(self, message: str, is_warning: bool = False) -> None:
        """Display the message bar with confirm and cancel buttons.

        display message in warning style if `is_warning` is set to True.
        """
        self.message_bar.displayPrompt(message, is_warning)
        self.stacked_widget.setCurrentWidget(self.message_bar)

    def onBrowseDir(self) -> None:
        """Browse and set backup directory."""
        selected_dir = QFileDialog.getExistingDirectory(
            self, "Select backup directory", "",
        )
        if not selected_dir:
            return  # no dir selected.
        self.backup_dir = selected_dir
        self.action_widget.label.setText(f"Backup dir: {selected_dir}")
