import os
import shutil
import subprocess
from typing import Generator

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QFrame, QMessageBox, QProgressBar, QStackedWidget,
                             QVBoxLayout, QWidget)

import styles
from utils.power import PROCESS_STARTUP_INFO

from .border_widget import BorderWidget
from .drivers_view import DriversView, Thread
from .error_view import ErrorView
from .loading_widget import LoadingWidget


class DriversBackup(QFrame):
    signal = pyqtSignal(int)
    signal1 = pyqtSignal(int, int)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self._parent = parent
        self._backup_dir = os.path.join(os.getcwd(), 'drivers-backup')
        self.setupWidgets()
        self.setStyleSheet(styles.get("drivers"))
        self.__backup_thread: Thread | None = None
        self.__uninstall_thread: Thread | None = None

    def setupWidgets(self) -> None:
        """Setup the widgets in layout"""
        self.stacked_widget = QStackedWidget(self)
        self.loading_widget = LoadingWidget(self.stacked_widget)

        self.main_widget = QWidget(self.stacked_widget)
        self.drivers_view = DriversView(self.main_widget)
        self.drivers_view.connect(self.setMainWidget)
        self.drivers_view.connectUninstall(self.startUninstall)

        self.border_widget = BorderWidget(self.main_widget, self._backup_dir)
        self.border_widget.connectBackup(
            lambda: self.startBackup(self.drivers_view.selectedItems())
        )

        vlayout = QVBoxLayout(self.main_widget)
        vlayout.addWidget(self.drivers_view)
        vlayout.addWidget(self.border_widget)
        vlayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        vlayout.setContentsMargins(0, 0, 0, 0)
        self.main_widget.setLayout(vlayout)

        self.stacked_widget.addWidget(self.loading_widget)
        self.stacked_widget.addWidget(self.main_widget)

        layout = QVBoxLayout(self)
        layout.addWidget(self.stacked_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def setMainWidget(self) -> None:
        """Set main driver widget"""
        self.stacked_widget.setCurrentWidget(self.main_widget)
        self.stacked_widget.removeWidget(self.loading_widget)
        self.loading_widget.deleteLater()

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
        # hide progressbar on finish
        self.border_widget.switchToMain()

    def startBackup(self, selected_drivers: Generator[list[str], None, None]) -> None:
        """Start drivers backup in new thread"""
        if self.__backup_thread and self.__backup_thread.isRunning():
            self.showBackupWarning()
            return
        if self.showDirExistsWarning():
            return  # on cancel
        self.failed_drivers: list[tuple[str, str, str]] = []
        drivers = list(selected_drivers)
        self.__backup_thread = Thread(self.backupDrivers, drivers)
        self.__backup_thread.start()
        self.__backup_thread.finished.connect(  # type: ignore
            lambda: self.onBackupFinish(drivers)
        )
        self.progressbar.setRange(0, len(drivers))
        self.progressbar.setFormat("backing up drivers: %v/%m (%p%)")
        self.border_widget.showProgressBar()  # show on progress start
        self.signal.connect(self.updateProgressbar)

    def startUninstall(self, row: int) -> None:
        """Start driver uninstall in new thread"""
        if self.__uninstall_thread and self.__uninstall_thread.isRunning():
            self.showUninstallWarning()
            return
        self.__uninstall_thread = Thread(self.uninstallDriver, row)
        self.__uninstall_thread.start()
        self.signal1.connect(self.onUninstallFinish)

        if not (self.__backup_thread and self.__backup_thread.isRunning()):
            self.border_widget.displayMessage(
                f"Uninstalling Driver: {self.drivers_view.drivers[row][0]}"
            )

    def backupDrivers(self, drivers: list[list[str]]) -> None:
        """Backup 3rd party driver packages from the driver store.

        using pnputil - Microsoft PnP Utility
        """
        for idx, (published_name, original_name, *_) in enumerate(drivers):
            driver_dir = os.path.join(self.backup_dir,
                                      f"{published_name}_{original_name}")
            os.makedirs(driver_dir, exist_ok=True)
            process = subprocess.Popen(
                ["pnputil", "/export-driver", published_name, driver_dir],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                startupinfo=PROCESS_STARTUP_INFO
            )
            self.signal.emit(idx)  # update progressbar
            if not process.wait():
                continue  # on success
            stdout, stderr = process.communicate()
            error = stdout or stderr
            self.failed_drivers.append(
                (published_name, original_name, error.decode())
            )

    def uninstallDriver(self, row: int) -> None:
        """uninstall driver package using pnputil"""
        published_name = self.drivers_view.drivers[row][0]
        process = subprocess.Popen(
            ["pnputil", "/uninstall", "/delete-driver", published_name, "/force"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            startupinfo=PROCESS_STARTUP_INFO
        )
        self.signal1.emit(process.wait(), row)

    def onBackupFinish(self, drivers: list[list[str]]) -> None:
        """Show message and copy install-script to backup directory"""
        if not self.failed_drivers:
            self.border_widget.displayMessage(
                f"Backed up drivers to {self.backup_dir!r}")
        else:
            ratio = f"{len(self.failed_drivers)}/{len(drivers)}"
            self.border_widget.displayPrompt(
                f"Failed to backup {ratio} drivers, Do you want to see them?")
            self.border_widget.message_overlay.connect(
                lambda: ErrorView(
                    self.main_widget, self.stacked_widget, self.failed_drivers)
            )
        # copy installation script to backup directory
        script_file = "./INSTALL-DRIVERS.bat"
        destination_file = os.path.join(self.backup_dir, script_file)
        shutil.copy(script_file, destination_file)

    def onUninstallFinish(self, status: int, row: int) -> None:
        """Remove the selected row and disconnect the signal"""
        self.signal1.disconnect(self.onUninstallFinish)
        published_name = self.drivers_view.drivers[row][0]
        if not status:  # remove row on success
            self.drivers_view.model().removeRow(row)
            self.border_widget.displayMessage(
                f"Successively Uninstalled Driver: {published_name}")
            return

        if not (self.__backup_thread and self.__backup_thread.isRunning()):
            self.border_widget.displayMessage(
                f"Failed to uninstall driver: {published_name}, status code: {status}", True
            )
            return
        QMessageBox.warning(
            self, "Failed to uninstall driver",
            f"Couldn't uninstall driver: {published_name}\
                \nFailed with status code: {status}",
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Ok
        )

    def showBackupWarning(self) -> None:
        """Show backup already running warning"""
        QMessageBox.warning(
            self, "Can't run another backup",
            "Already backing up drivers.",
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Ok
        )

    def showUninstallWarning(self) -> None:
        """Show uninstall already running warning"""
        QMessageBox.warning(
            self, "Can't run another uninstall",
            "Already uninstalling driver.",
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Ok
        )

    def showDirExistsWarning(self) -> bool:
        """Show warning if backup directory already exists.

        Return:
            True on cancel else False
        """
        if not os.path.exists(self.backup_dir):
            return False  # if doesn't exist
        try:
            next(os.scandir(self.backup_dir))
        except StopIteration:
            return False  # if empty

        answer = QMessageBox.warning(
            self, "Backup directory already exists",
            "Contents in directory will be overwritten\n \
            Do you want to proceed?",
            QMessageBox.StandardButton.Cancel |
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Cancel
        )
        if answer != QMessageBox.StandardButton.Ok:
            return True
        return False
