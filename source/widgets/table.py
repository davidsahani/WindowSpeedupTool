from typing import Any, Final, MutableSequence, override, Sequence

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, QRect, Qt
from PyQt6.QtGui import QMouseEvent, QPainter
from PyQt6.QtWidgets import (
    QCheckBox,
    QHeaderView,
    QStyle,
    QStyleOptionButton,
    QTableView,
    QWidget,
)


class TableModel(QAbstractTableModel):
    def __init__(self, data: MutableSequence[Any], header_names: Sequence[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data = data
        self._header_names = header_names

    @override
    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            return self._data[index.row()][index.column()]

    @override
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._data)

    @override
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._data[0]) if self._data else 0

    @override
    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: int = Qt.ItemDataRole.DisplayRole) -> str | int | None:

        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Vertical:
            return section + 1
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._header_names[section]


CHECK_STATE_ROLE: Final = 65535


class CheckableTableModel[T](TableModel):
    def __init__(self, data: MutableSequence[T], header_names: Sequence[str], parent: QWidget | None = None) -> None:
        super().__init__(data, header_names, parent)
        self._check_states = [Qt.CheckState.Checked] * len(data)

    @override
    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole | Qt.ItemDataRole.CheckStateRole) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            return self._data[index.row()][index.column()]
        if role == CHECK_STATE_ROLE and index.column() == 0:
            return self._check_states[index.row()]

    @override
    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        if role == CHECK_STATE_ROLE and index.column() == 0:
            self._check_states[index.row()] = value
        return True

    @override
    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if index.column() == 0:
            return super().flags(index) | Qt.ItemFlag.ItemIsUserCheckable
        return super().flags(index)

    @override
    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: int = Qt.ItemDataRole.DisplayRole) -> str | int | None:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Vertical:
            return ' ' * 5  # spaces for checkbox
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._header_names[section]

    @override
    def removeRow(self, row: int, parent: QModelIndex = QModelIndex()) -> bool:
        self.beginRemoveRows(parent, row, row)
        self.endRemoveRows()
        try:
            self._data.pop(row)
            self._check_states.pop(row)
        except IndexError:
            return False
        else:
            return True

    def selectedItems(self) -> list[T]:
        return [item for item, state in zip(self._data, self._check_states) if state == Qt.CheckState.Checked]


class CustomCheckBox(QCheckBox):
    def __init__(self, parent: QWidget, checked: bool) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            """QCheckBox::indicator {
                width: 16px;
                height: 18px;
                margin: 0px;
                padding: 0px;
            }
            """
        )
        self.setChecked(checked)
        size = self.sizeHint()
        self.setGeometry(11, 2, size.width(), size.height())


class CheckableHeaderView(QHeaderView):
    def __init__(self, parent: QTableView, orientation: Qt.Orientation = Qt.Orientation.Vertical,
                 *, all_checked: bool = False) -> None:
        super().__init__(orientation, parent)
        model = parent.model()
        if model is None:
            raise ValueError(
                f"Could not retrieve model from: {parent.__class__.__name__}"
            )
        self._model = model
        self.all_checkbox = CustomCheckBox(parent, all_checked)
        self.all_checkbox.clicked.connect(self.updateCheckBoxes)
        _ = not all_checked and not self.updateCheckBoxes(all_checked)

    @override
    def paintSection(self, painter: QPainter | None, rect: QRect, logicalIndex: int) -> None:
        if painter is None:
            return super().paintSection(painter, rect, logicalIndex)

        painter.save()
        super().paintSection(painter, rect, logicalIndex)
        painter.restore()
        painter.translate(rect.topLeft())

        option = QStyleOptionButton()
        option.rect = QRect(10, 10, 10, 10)

        index = self._model.index(logicalIndex, 0)
        check_state = self._model.data(index, CHECK_STATE_ROLE)
        if check_state == Qt.CheckState.Checked:
            option.state = QStyle.StateFlag.State_On
        else:
            option.state = QStyle.StateFlag.State_Off

        style = self.style()
        if style is not None:
            style.drawControl(QStyle.ControlElement.CE_CheckBox, option, painter)  # noqa

    @override
    def mousePressEvent(self, e: QMouseEvent | None) -> None:
        model = self.model()
        if e is not None and model is not None:
            index = self.logicalIndexAt(e.pos())
            model_index = model.index(index, 0)
            current_state = model.data(model_index, CHECK_STATE_ROLE)
            new_state = Qt.CheckState.Unchecked if current_state == \
                Qt.CheckState.Checked else Qt.CheckState.Checked
            model.setData(model_index, new_state, CHECK_STATE_ROLE)
            self.updateSection(index)
        super().mousePressEvent(e)

    def updateCheckBoxes(self, checked: bool) -> None:
        new_state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for idx in range(self._model.rowCount()):
            model_index = self._model.index(idx, 0)
            self._model.setData(model_index, new_state, CHECK_STATE_ROLE)
            self.updateSection(idx)
