import subprocess
from typing import Callable, Generator

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QContextMenuEvent
from PyQt6.QtWidgets import (QHeaderView, QMenu, QMessageBox, QTableView,
                             QWidget)

from src.process_terminal import Thread
from src.table import CheckableHeaderView, Model
from utils.power import PROCESS_STARTUP_INFO


class LoadDrivers:
    valueChanged = pyqtSignal(list)

    def __init__(self) -> None:
        self.__thread: Thread | None = None
        self.drivers: list[list[str]] = []
        self.__functions: list[Callable[[], None]] = []

    def startLoadDrivers(self) -> None:
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
        cmd = ["Dism", "/online", "/get-drivers", "/format:table"]
        output = subprocess.check_output(
            cmd, startupinfo=PROCESS_STARTUP_INFO).decode()

        for line in output.splitlines():
            values = line.split('|')
            if not values[0].rstrip().endswith('.inf'):
                continue
            self.valueChanged.emit([v.strip() for v in values])  # type: ignore

    def insertValues(self, values: list[str]) -> None:
        """Append values into drivers"""
        self.drivers.append(values)

    def onFinish(self) -> None:
        """Run the connected functions on thread finish"""
        for function in self.__functions:
            function()

    def connect(self, function: Callable[[], None]) -> None:
        """Connect the function to thread finish event"""
        self.__functions.append(function)


class DriversView(QTableView, LoadDrivers):
    def __init__(self, parent: QWidget) -> None:
        QTableView.__init__(self, parent)
        LoadDrivers.__init__(self)
        self.startLoadDrivers()
        # setup table on thread finish
        self.connect(self.setupTable)
        self.__function = None  # for uninstall

    def setupTable(self) -> None:
        header_names = ["Published Name", "Original File Name", "Inbox",
                        "Class Name", "Provider Name", "Date", "Version"]

        self.setModel(Model(self, self.drivers, header_names))
        # Set column resizing
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Custom)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)

        self.header = CheckableHeaderView(self, all_checked=True)
        self.setVerticalHeader(self.header)
        self.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

    def contextMenuEvent(self, a0: QContextMenuEvent) -> None:
        index = self.indexAt(a0.pos())
        if not index.isValid():
            return
        menu = QMenu(self)
        uninstall_action = menu.addAction("Uninstall Driver")
        action = menu.exec(self.mapToGlobal(a0.pos()))
        if action == uninstall_action:
            self.uninstallAction(index.row())

    def uninstallAction(self, row: int) -> None:
        answer = QMessageBox.warning(
            self, "Are you sure you want to uninstall this driver?",
            "This driver can't be restored after you uninstall it.",
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

    def selectedItems(self) -> Generator[list[str], None, None]:
        """yield the selected items from model"""
        for index, state in enumerate(self.header.check_states):
            if not state:
                continue   # for unselected items
            yield self.drivers[index]
