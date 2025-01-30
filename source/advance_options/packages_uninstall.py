from typing import override

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QMessageBox, QVBoxLayout, QWidget

from utils import styles
from utils.threads import CommandThread, Result
from widgets.loading_widget import LoadingWidget
from widgets.message_bar import MessageBar
from widgets.process_terminal import ProcessTerminal
from widgets.sizegrip import SizeGrip
from widgets.stacked_widget import StackedWidget

from .packages_view import PackagesView


class Terminal(ProcessTerminal):
    @override
    def showWarning(self) -> None:
        QMessageBox.warning(
            self, "Can't run another uninstall",
            "Already uninstalling package.",
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Ok
        )


def format_output(output: str) -> list[list[str]]:
    result: list[list[str]] = []
    for line in output.splitlines():
        values = line.split('|')
        if not values:
            continue
        if not values[-1].rstrip().endswith(('AM', 'PM')):
            continue
        result.append([v.strip() for v in values])
    return result


class PackagesUninstall(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setupThread()
        self.setupWidgets()
        self.setStyleSheet(styles.get("drivers"))
        self.load_packages_thread.start()

    def setupThread(self) -> None:
        self.load_packages_thread = CommandThread(
            ["dism", "/online", "/get-packages", "/format:table"]
        )
        self.load_packages_thread.connect(self.setMainWidget)

    def setupWidgets(self) -> None:
        loading_widget = LoadingWidget("Loading Packages...")
        self.message_bar = MessageBar(False)
        self.message_bar.setRetryStyleForCloseButton(True)
        self.message_bar.connectClose(self.load_packages_thread.start)

        self.stacked_widget = StackedWidget(self)
        self.stacked_widget.addWidget(loading_widget, dispose=True)

        layout = QVBoxLayout(self)
        layout.addWidget(self.stacked_widget)
        layout.addWidget(self.message_bar)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def setMainWidget(self, result: Result[str]) -> None:
        """Set the main packages widget."""
        if result.value is None:
            self.message_bar.displayMessage(result.error.stderr, True)
            return

        packages = format_output(result.value)
        if not packages:
            return self.message_bar.displayMessage(
                "Error retrieving packages from command: " +
                " ".join(self.load_packages_thread.command), True
            )

        self.packages_view = PackagesView(packages)
        self.packages_view.connectUninstall(self.startUninstall)

        self.terminal = Terminal()
        size_grip = SizeGrip(self.terminal)
        size_grip.hide()      # hide initially.
        self.terminal.hide()  # hide initially.

        self.main_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.packages_view)
        layout.addWidget(size_grip)
        layout.addWidget(self.terminal)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)
        self.main_widget.setLayout(layout)

        self.stacked_widget.addWidget(self.main_widget)
        self.stacked_widget.setCurrentWidget(self.main_widget)

    def startUninstall(self, row: int) -> None:
        """Start package uninstall in terminal."""
        self.terminal.runCommand(
            ["Dism", "/Online", "/Remove-Package",
                f"/PackageName:{self.packages_view.packages[row][0]}"]
        )
        self.terminal.connectFinish(
            lambda s: self.onUninstallFinish(s, row))

    def onUninstallFinish(self, status: int, row: int) -> None:
        """Remove the selected row from the model."""
        model = self.packages_view.model()
        if status != 0 or model is None:
            return  # on failure
        model.removeRow(row)
