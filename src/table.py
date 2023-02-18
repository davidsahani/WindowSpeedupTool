from PyQt6.QtCore import QAbstractTableModel, QModelIndex, QRect, Qt
from PyQt6.QtGui import QMouseEvent, QPainter
from PyQt6.QtWidgets import (QHeaderView, QStyle, QStyleOptionButton,
                             QTableView, QWidget)


class Model(QAbstractTableModel):
    def __init__(self, parent: QWidget, data: list[list[str]], header_names: list[str]) -> None:
        super().__init__(parent)
        self._data = data
        self.header_names = header_names

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> str | None:
        if role == Qt.ItemDataRole.DisplayRole:
            return self._data[index.row()][index.column()]

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._data[0])

    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: int = Qt.ItemDataRole.DisplayRole) -> str | int | None:

        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Vertical:
            return ' ' * 5  # spaces for checkbox
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.header_names[section]

    def removeRow(self, row: int, parent: QModelIndex = QModelIndex()) -> bool:
        self.beginRemoveRows(parent, row, row)
        del self._data[row]
        self.endRemoveRows()
        return True


class CheckableHeaderView(QHeaderView):
    def __init__(self, parent: QTableView, orientation: Qt.Orientation = Qt.Orientation.Vertical,
                 *, all_checked: bool = False) -> None:
        super().__init__(orientation, parent)
        self.check_states = [all_checked] * parent.model().rowCount()

    def paintSection(self, painter: QPainter, rect: QRect, logicalIndex: int) -> None:
        painter.save()
        super().paintSection(painter, rect, logicalIndex)
        painter.restore()
        painter.translate(rect.topLeft())

        option = QStyleOptionButton()
        option.rect = QRect(10, 10, 10, 10)

        if self.check_states[logicalIndex]:
            option.state = QStyle.StateFlag.State_On
        else:
            option.state = QStyle.StateFlag.State_Off
        self.style().drawControl(QStyle.ControlElement.CE_CheckBox, option, painter)

    def mousePressEvent(self, e: QMouseEvent) -> None:
        index = self.logicalIndexAt(e.pos())
        self.check_states[index] = not self.check_states[index]
        self.updateSection(index)
        super().mousePressEvent(e)
