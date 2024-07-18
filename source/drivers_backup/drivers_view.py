from typing import Any, Callable, override

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QContextMenuEvent
from PyQt6.QtWidgets import QHeaderView, QMenu, QMessageBox, QTableView, QWidget

from widgets.table import CheckableHeaderView, CheckableTableModel


class DriversView(QTableView):
    _uninstall = pyqtSignal(int)

    def __init__(self, drivers: list[list[str]], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.drivers = drivers
        self.setupTable()

    def setupTable(self) -> None:
        header_names = ["Published Name", "Original File Name", "Inbox",
                        "Class Name", "Provider Name", "Date", "Version"]

        self.checkable_model = CheckableTableModel(self.drivers, header_names)
        self.setModel(self.checkable_model)  # set checkable table model.
        self.setVerticalHeader(CheckableHeaderView(self, all_checked=True))
        self.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

        # set column resizing
        header = self.horizontalHeader()
        if header is None:
            return
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Custom)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)

    @override
    def contextMenuEvent(self, a0: QContextMenuEvent | None) -> None:
        if a0 is None:
            return
        menu = QMenu(self)
        index = self.indexAt(a0.pos())
        uninstall_action = menu.addAction("Uninstall Driver")  # type: ignore
        action = menu.exec(self.mapToGlobal(a0.pos()))
        if action == uninstall_action and action is not None and index.isValid():
            self.uninstallAction(index.row())

    def uninstallAction(self, row: int) -> None:
        answer = QMessageBox.warning(
            self, "Are you sure you want to uninstall this driver?",
            "This driver can't be recovered after you uninstall it.",
            QMessageBox.StandardButton.Cancel |
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Cancel
        )
        if answer == QMessageBox.StandardButton.Cancel:
            return  # on cancel
        self._uninstall.emit(row)

    def connectUninstall(self, function: Callable[[int], Any]) -> None:
        """Connect the function to uninstall action event.

        Receive:
            current selected row
        """
        self._uninstall.connect(function)

    def publishedName(self, row: int) -> str:
        """Get published name from model."""
        return self.drivers[row][0]

    def selectedItems(self) -> list[list[str]]:
        """Return the selected items from model."""
        return self.checkable_model.selectedItems()
