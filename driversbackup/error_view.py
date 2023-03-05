from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt6.QtWidgets import (QHeaderView, QStackedWidget, QTableView,
                             QVBoxLayout, QWidget)

from widgets.overlay import MessageOverlay


class TableModel(QAbstractTableModel):
    def __init__(self, parent: QWidget, errors: list[tuple[str, str, str]]) -> None:
        super().__init__(parent)
        self.errors = errors

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> str | None:
        if role == Qt.ItemDataRole.DisplayRole:
            return self.errors[index.row()][index.column()]

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.errors)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.errors[0])

    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: int = Qt.ItemDataRole.DisplayRole) -> str | int | None:

        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Vertical:
            return section + 1
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return ["Published Name", "Original File Name", "Error Message"][section]


class TableView(QTableView):
    def __init__(self, parent: QWidget, errors: list[tuple[str, str, str]]) -> None:
        super().__init__(parent)
        self.errors = errors
        self.setupTable()

    def setupTable(self) -> None:
        model = TableModel(self, self.errors)
        self.setModel(model)
        # Set column resizing
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)


# *================================================
# *             ERROR VIEW WIDGET                 *
# *================================================


class ErrorView(QWidget):
    def __init__(self, master: QWidget, parent: QStackedWidget, errors: list[tuple[str, str, str]]) -> None:
        super().__init__(parent)
        self._master = master
        self._parent = parent
        self.errors = errors
        self.setupWidgets()
        self.addSelf()

    def addSelf(self) -> None:
        """Add self to stacked widget"""
        self.__just_entered = True
        self._parent.addWidget(self)
        self._parent.setCurrentWidget(self)
        self._parent.currentChanged.connect(self.removeSelf)  # type: ignore

    def removeSelf(self) -> None:
        """Remove self from stacked widget on change"""
        if self.__just_entered:
            self.__just_entered = False
            return
        self._parent.removeWidget(self)
        self.deleteLater()  # delete this widget when changed

    def switchToMaster(self) -> None:
        """Switch to master widget"""
        self._parent.setCurrentWidget(self._master)

    def setupWidgets(self) -> None:
        """Setup the widgets in layout"""
        view = TableView(self, self.errors)
        message_overlay = MessageOverlay(self, False)
        message_overlay.connectClose(self.switchToMaster)
        message_overlay.displayMessage("Failed to backup these drivers", True)

        layout = QVBoxLayout(self)
        layout.addWidget(view)
        layout.addWidget(message_overlay)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setAlignment(message_overlay, Qt.AlignmentFlag.AlignBottom)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
