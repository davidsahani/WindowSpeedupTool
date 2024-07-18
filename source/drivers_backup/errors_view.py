from typing import Any, Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHeaderView, QTableView, QVBoxLayout, QWidget

from widgets.message_bar import MessageBar
from widgets.table import TableModel


class TableView(QTableView):
    def __init__(self, parent: QWidget, errors: list[tuple[str, str, str]]) -> None:
        super().__init__(parent)
        self.errors = errors
        self.setupTable()

    def setupTable(self) -> None:
        header_names = \
            ["Published Name", "Original File Name", "Error Message"]
        self.setModel(TableModel(self.errors, header_names))
        # set column resizing
        header = self.horizontalHeader()
        if header is None:
            return
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)


# *================================================
# *             ERRORS VIEW WIDGET                *
# *================================================


class ErrorsView(QWidget):
    def __init__(self, parent: QWidget, errors: list[tuple[str, str, str]]) -> None:
        super().__init__(parent)
        self.errors = errors
        self.setupWidgets()

    def setupWidgets(self) -> None:
        """Setup the widgets in layout."""
        view = TableView(self, self.errors)
        self.message_bar = MessageBar(False)
        self.message_bar.displayMessage(
            "Failed to backup these drivers...", True
        )

        layout = QVBoxLayout(self)
        layout.addWidget(view)
        layout.addWidget(self.message_bar)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setAlignment(self.message_bar, Qt.AlignmentFlag.AlignBottom)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def connectClose(self, function: Callable[[], Any]) -> None:
        """Connect the function to close button press event."""
        self.message_bar.connectClose(function)
