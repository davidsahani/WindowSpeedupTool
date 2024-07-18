import os
import shutil

from PyQt6.QtCore import pyqtSignal, QMutex, QMutexLocker, Qt
from PyQt6.QtWidgets import QFrame, QMessageBox, QProgressBar, QVBoxLayout, QWidget

from utils import config, styles
from utils.threads import CommandThread, Result, Thread
from widgets.loading_widget import LoadingWidget
from widgets.message_bar import MessageBar
from widgets.stacked_widget import StackedWidget

from .border_widget import BorderWidget
from .drivers_view import DriversView
from .errors_view import ErrorsView


def get_backup_dir() -> str:
    path = os.path.join(os.environ.get('USERPROFILE') or '', 'documents')
    if not os.path.exists(path):
        path = os.getcwd()
    return os.path.join(path, 'drivers-backup')


def format_output(output: str) -> list[list[str]]:
    result: list[list[str]] = []
    for line in output.splitlines():
        values = line.split('|')
        if not values:
            continue
        if not values[0].rstrip().endswith('.inf'):
            continue
        result.append([v.strip() for v in values])
    return result


class DriversBackup(QFrame):
    progress = pyqtSignal(int)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self._backup_dir = get_backup_dir()
        self.setupThreads()
        self.setupWidgets()
        self.setStyleSheet(styles.get("drivers"))
        self.__mutex = QMutex()
        self.__cancel_flag = False
        self.load_drivers_thread.start()

    def setupThreads(self) -> None:
        self.backup_thread = None
        self.uninstall_thread = None

        self.load_drivers_thread = CommandThread(
            ["dism", "/online", "/get-drivers", "/format:table"]
        )
        self.load_drivers_thread.connect(self.setMainWidget)

    def setupWidgets(self) -> None:
        loading_widget = LoadingWidget("Loading Drivers...")
        self.message_bar = MessageBar(False)
        self.message_bar.setRetryStyleForCloseButton(True)
        self.message_bar.connectClose(self.load_drivers_thread.start)

        self.stacked_widget = StackedWidget(self)
        self.stacked_widget.addWidget(loading_widget, dispose=True)

        layout = QVBoxLayout(self)
        layout.addWidget(self.stacked_widget)
        layout.addWidget(self.message_bar)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def setMainWidget(self, result: Result[str]) -> None:
        """Set the main driver widget."""
        if result.value is None:
            self.message_bar.displayMessage(result.error.stderr, True)
            return

        drivers = format_output(result.value)
        if not drivers:
            return self.message_bar.displayMessage(
                "Error retrieving drivers from command: " +
                " ".join(self.load_drivers_thread.command), True
            )

        self.drivers_view = DriversView(drivers)
        self.drivers_view.connectUninstall(self.startUninstall)

        self.border_widget = BorderWidget(self, self._backup_dir)
        self.border_widget.connectBackup(
            lambda: self.startBackup(self.drivers_view.selectedItems())
        )
        self.border_widget.cancel_button.clicked.connect(self.cancel)

        self.main_widget = QWidget()
        layout = QVBoxLayout(self.main_widget)
        layout.addWidget(self.drivers_view)
        layout.addWidget(self.border_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)
        self.main_widget.setLayout(layout)

        self.stacked_widget.addWidget(self.main_widget)
        self.stacked_widget.setCurrentWidget(self.main_widget)

    @property
    def progressbar(self) -> QProgressBar:
        return self.border_widget.progressbar

    @property
    def backup_dir(self) -> str:
        return self.border_widget.backup_dir

    def updateProgressbar(self, value: int) -> None:
        """Update the progressbar"""
        self.progressbar.setValue(value)
        if value < self.progressbar.maximum():
            return
        # hide progressbar on finish.
        self.border_widget.showMainWidget()

    def cancel(self) -> None:
        with QMutexLocker(self.__mutex):
            self.__cancel_flag = True

    def is_cancelled(self) -> bool:
        with QMutexLocker(self.__mutex):
            return self.__cancel_flag

    def reset_cancel(self) -> None:
        with QMutexLocker(self.__mutex):
            self.__cancel_flag = False

    def startBackup(self, selected_drivers: list[list[str]]) -> None:
        """Start drivers backup in new thread."""
        if self.backup_thread and self.backup_thread.isRunning():
            self.showBackupRunningWarning()
            return
        if self.showDirExistsWarning():
            return  # on cancel

        self.failed_drivers: list[tuple[str, str, str]] = []

        self.backup_thread = Thread(self.backupDrivers, selected_drivers)
        self.backup_thread.finished.connect(
            lambda: self.onBackupFinish(selected_drivers)
        )
        self.reset_cancel()
        self.backup_thread.start()

        self.progressbar.setRange(0, len(selected_drivers))
        self.progressbar.setFormat("Backing up drivers: %v/%m (%p%)")
        self.border_widget.showProgressBar()  # show on progress start.
        self.progress.connect(self.updateProgressbar)

    def startUninstall(self, row: int) -> None:
        """Start driver uninstall in new thread."""
        if self.uninstall_thread and self.uninstall_thread.isRunning():
            self.showUninstallRunningWarning()
            return

        published_name = self.drivers_view.publishedName(row)
        self.uninstall_thread = CommandThread(
            ["pnputil", "/uninstall", "/delete-driver", published_name, "/force"]
        )
        self.uninstall_thread.connect(
            lambda result: self.onUninstallFinish(result, row)
        )
        if not (self.backup_thread and self.backup_thread.isRunning()):
            self.border_widget.displayMessage(
                f"Uninstalling Driver: {published_name}"
            )
        self.uninstall_thread.start()

    def backupDrivers(self, drivers: list[list[str]]) -> None:
        """Backup 3rd party driver packages from the driver store.

        using pnputil - Microsoft PnP Utility
        """
        for idx, (published_name, original_name, *_) in enumerate(drivers):
            if self.is_cancelled():
                break
            driver_dir = os.path.join(
                self.backup_dir, f"{published_name}_{original_name}"
            )
            os.makedirs(driver_dir, exist_ok=True)

            result = Result.from_command(
                ["pnputil", "/export-driver", published_name, driver_dir]
            )
            if result.value is None:
                self.failed_drivers.append(
                    (published_name, original_name, result.error.stderr)
                )
            self.progress.emit(idx)

    def onBackupFinish(self, drivers: list[list[str]]) -> None:
        """Show message and copy install-script to backup directory."""
        if not self.failed_drivers:
            self.border_widget.displayMessage(
                f"Backed up drivers to: {self.backup_dir}")
        else:
            ratio = f"{len(self.failed_drivers)}/{len(drivers)}"
            self.border_widget.displayPrompt(
                f"Failed to backup {ratio} drivers, Do you want to see them?"
            )
            self.border_widget.message_bar.connect(self.openErrorView)

        # copy installation script to backup directory.
        install_script = "INSTALL-DRIVERS.bat"
        install_script_file = os.path.join(config.PROJECT_DIR, install_script)
        destination_file = os.path.join(self.backup_dir, install_script)
        if os.path.exists(install_script_file):
            return shutil.copy2(install_script_file, destination_file)

        QMessageBox.warning(
            self, "Failed to copy install script",
            f"Install-Script: {install_script} not found.\n" +
            f"In directory: {config.PROJECT_DIR}",
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Ok
        )

    def onUninstallFinish(self, result: Result[str], row: int) -> None:
        """Remove the selected row and show status message"""
        published_name = self.drivers_view.publishedName(row)
        if result.value is not None:
            self.border_widget.showMainWidget()

            QMessageBox.warning(
                self, f"Failed to uninstall driver: {published_name}",
                result.error.stderr,
                QMessageBox.StandardButton.Ok,
                QMessageBox.StandardButton.Ok
            )
            return

        message = f"Successively Uninstalled Driver: {published_name}"

        model = self.drivers_view.model()
        if model is not None:
            model.removeRow(row)
        else:
            message = f"Entry Removal Failed!, {message}"

        self.border_widget.displayMessage(message)

    def showBackupRunningWarning(self) -> None:
        """Show backup already running warning."""
        QMessageBox.warning(
            self, "Can't run another backup",
            "Already backing up drivers.",
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Ok
        )

    def showUninstallRunningWarning(self) -> None:
        """Show uninstall already running warning."""
        QMessageBox.warning(
            self, "Can't run another uninstall",
            "Already uninstalling driver.",
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Ok
        )

    def showDirExistsWarning(self) -> bool:
        """Show warning if backup directory already exists.

        Return:
            True on cancel otherwise False.
        """
        if not os.path.exists(self.backup_dir):
            return False  # directory doesn't exist.
        try:
            next(os.scandir(self.backup_dir))
        except StopIteration:
            return False  # directory is empty.

        answer = QMessageBox.warning(
            self, "Backup directory already exists",
            "Contents in directory will be overwritten\n" +
            "Do you want to proceed?",
            QMessageBox.StandardButton.Cancel |
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Cancel
        )
        return answer == QMessageBox.StandardButton.Cancel

    def openErrorView(self) -> None:
        """Open errors view widget."""
        self.errors_view = ErrorsView(self.stacked_widget, self.failed_drivers)
        self.stacked_widget.addWidget(self.errors_view, dispose=True)
        self.stacked_widget.setCurrentWidget(self.errors_view)
        self.errors_view.connectClose(lambda: (  # switch to main widget.
            self.stacked_widget.setCurrentWidget(self.main_widget),
            self.border_widget.showMainWidget()
        ))
