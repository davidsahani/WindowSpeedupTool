import subprocess
from typing import Callable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QContextMenuEvent
from PyQt6.QtWidgets import (QHeaderView, QMenu, QMessageBox, QTableView,
                             QWidget)

from utils.power import PROCESS_STARTUP_INFO
from widgets.process_terminal import Thread
from widgets.table import Model


class LoadPackages:
    valueChanged = pyqtSignal(list)

    def __init__(self) -> None:
        self.__thread: Thread | None = None
        self.packages: list[list[str]] = []
        self.__functions: list[Callable[[], None]] = []

    def startLoadPackages(self) -> None:
        """Run load drivers in new thread."""
        if self.__thread and self.__thread.isRunning():
            return
        self.__thread = Thread(self.loadDrivers)
        self.__thread.start()
        self.valueChanged.connect(self.insertValues)  # type: ignore
        self.__thread.finished.connect(  # type: ignore
            lambda: self.valueChanged.disconnect(  # type: ignore
                self.insertValues)
        )
        self.__thread.finished.connect(self.onFinish)  # type: ignore

    def loadDrivers(self) -> None:
        """Load system drivers"""
        cmd = ["Dism", "/online", "/get-packages", "/format:table"]
        output = subprocess.check_output(
            cmd, startupinfo=PROCESS_STARTUP_INFO).decode()

        for line in output.splitlines():
            values = line.split('|')
            if not values[-1].rstrip().endswith(('AM', 'PM')):
                continue
            self.valueChanged.emit([v.strip() for v in values])  # type: ignore

    def insertValues(self, values: list[str]) -> None:
        """Append values into packages"""
        self.packages.append(values)

    def onFinish(self) -> None:
        """Run the connected functions on thread finish"""
        for function in self.__functions:
            function()

    def connectFinish(self, function: Callable[[], None]) -> None:
        """Connect the function to thread finish event"""
        self.__functions.append(function)


class PackagesModel(Model):
    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: int = Qt.ItemDataRole.DisplayRole) -> str | int | None:

        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Vertical:
            return section + 1
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.header_names[section]


class PackagesView(QTableView, LoadPackages):
    def __init__(self, parent: QWidget) -> None:
        QTableView.__init__(self, parent)
        LoadPackages.__init__(self)
        self.startLoadPackages()
        # setup table on thread finish
        self.connectFinish(self.setupTable)
        self.__function = None  # for uninstall

    def setupTable(self) -> None:
        header_names = ["Package Identity",
                        "State", "Release Type", "Install Time"]
        self.setModel(PackagesModel(self, self.packages, header_names))
        # Set column resizing
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Custom)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

    def contextMenuEvent(self, a0: QContextMenuEvent) -> None:
        index = self.indexAt(a0.pos())
        if not index.isValid():
            return
        menu = QMenu(self)
        uninstall_action = menu.addAction("Uninstall Package")
        action = menu.exec(self.mapToGlobal(a0.pos()))
        if action == uninstall_action:
            self.uninstallAction(index.row())

    def uninstallAction(self, row: int) -> None:
        answer = QMessageBox.warning(
            self, "Are you sure you want to uninstall this package?",
            "This package can't be restored after you uninstall it.",
            QMessageBox.StandardButton.Cancel |
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Cancel
        )
        if answer != QMessageBox.StandardButton.Ok:
            return
        function = self.__function
        if function is not None:
            function(row)

    def connectUninstall(self, function: Callable[[int], None]) -> None:
        """Connect the function to uninstall action event

        Receive:
            current selected row
        """
        self.__function = function
