from typing import Callable, override

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QContextMenuEvent
from PyQt6.QtWidgets import QHeaderView, QMenu, QMessageBox, QTableView, QWidget

from widgets.table import TableModel


class PackagesView(QTableView):
    _uninstall = pyqtSignal(int)

    def __init__(self, packages: list[list[str]], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.packages = packages
        self.setupTable()

    def setupTable(self) -> None:
        header_names = \
            ["Package Identity", "State", "Release Type", "Install Time"]
        self.setModel(TableModel(self.packages, header_names))
        self.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

        # set column resizing
        header = self.horizontalHeader()
        if header is None:
            return
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Custom)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

    @override
    def contextMenuEvent(self, a0: QContextMenuEvent | None) -> None:
        if a0 is None:
            return
        menu = QMenu(self)
        index = self.indexAt(a0.pos())
        uninstall_action = menu.addAction(  # type: ignore
            "Uninstall Package")
        action = menu.exec(self.mapToGlobal(a0.pos()))
        if action == uninstall_action and action is not None and index.isValid():
            self.uninstallAction(index.row())

    def uninstallAction(self, row: int) -> None:
        answer = QMessageBox.warning(
            self, "Are you sure you want to uninstall this package?",
            "This package can't be restored after you uninstall it.",
            QMessageBox.StandardButton.Cancel |
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Cancel
        )
        if answer == QMessageBox.StandardButton.Cancel:
            return  # on cancel
        self._uninstall.emit(row)

    def connectUninstall(self, function: Callable[[int], None]) -> None:
        """Connect the function to uninstall action event.

        Receive:
            current selected row
        """
        self._uninstall.connect(function)
