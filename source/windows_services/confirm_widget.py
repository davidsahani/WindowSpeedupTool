from typing import Any, Callable, override

from PyQt6.QtCore import QModelIndex, Qt
from PyQt6.QtWidgets import QHeaderView, QTableView, QVBoxLayout, QWidget

from utils import service
from widgets.message_bar import MessageBar
from widgets.stacked_widget import StackedWidget
from widgets.table import CheckableHeaderView, CheckableTableModel

from .services_thread import ServicesType


class CustomCheckableTableModel[T](CheckableTableModel[T]):
    @override
    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole | Qt.ItemDataRole.CheckStateRole | Qt.ItemDataRole.ToolTipRole) -> Any:
        if role == Qt.ItemDataRole.ToolTipRole and index.column() == 1:
            description = self._data[index.row()][-1]
            return f"<div <b>Description:</b> <p>{description}</p> </div>"
        return super().data(index, role)


class ServicesView(QTableView):
    def __init__(self, parent: QWidget, services: ServicesType,
                 show_curr_startup_type: bool) -> None:
        super().__init__(parent)
        self.services = services
        self.show_curr_startup_type = show_curr_startup_type
        self.setupTable()

    def setupTable(self) -> None:
        services_list: list[list[str]] = []

        for svc in self.services:
            startup_type = svc.startup_type

            if self.show_curr_startup_type:
                startup_type = service.startup_type(
                    svc.service_name).value or f"Unknown[{startup_type}]"

            result = service.info(svc.service_name)
            info = result.value or {}

            services_list.append([
                svc.service_name,
                info.get('display_name', svc.display_name),
                info.get('status', 'Unknown'),
                startup_type,
                info.get('username', 'Unknown'),
                info.get('description', result.error.stderr)
            ])

        self.services_list = services_list

        header_names = ["Service Name", "Display Name", "Status",
                        "Startup Type", "User", "Description"]

        self._model = CustomCheckableTableModel(services_list, header_names)
        self.setModel(self._model)  # set checkable tooltip table model.
        self.setVerticalHeader(CheckableHeaderView(self, all_checked=True))

        # set column resizing
        header = self.horizontalHeader()
        if header is None:
            return
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Custom)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)

    def selectedItems(self) -> list[list[str]]:
        """Return the selected services from model."""
        return self._model.selectedItems()


# *================================================
# *      SERVICES ACTION CONFIRMATION WIDGET      *
# *================================================


class ConfirmActionWidget(QWidget):
    def __init__(self, parent: StackedWidget, services: ServicesType,
                 show_curr_startup_type: bool) -> None:
        super().__init__(parent)
        self._parent = parent
        self.services = services
        self.show_curr_startup_type = show_curr_startup_type
        self.__function = None
        self.setupWidgets()

    def setupWidgets(self) -> None:
        """Setup the widgets in layout."""
        self.services_view = ServicesView(
            self, self.services, self.show_curr_startup_type
        )

        self.message_bar = MessageBar(False)
        self.message_bar.connect(self.onConfirm)
        self.message_bar.connectCancel(self._parent.switchToPreviousWidget)

        layout = QVBoxLayout()
        layout.addWidget(self.services_view)
        layout.addWidget(self.message_bar)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setAlignment(self.message_bar, Qt.AlignmentFlag.AlignBottom)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def onConfirm(self) -> None:
        """Handle confirm button press event."""
        function = self.__function
        if function is None:
            return
        service_names = {svc[0] for svc in self.services_view.selectedItems()}
        selected_services = [
            svc for svc in self.services if svc.service_name in service_names
        ]
        function(selected_services)  # pass in selected services from model
        self._parent.switchToPreviousWidget()  # switch back after confirmation

    def connect(self, function: Callable[[ServicesType], Any]) -> None:
        """Connect the function to prompt confirm button press event.

        Receive:
            selected services
        """
        self.__function = function

    def setConfirmText(self, text: str) -> None:
        """Set the text of the prompt confirm button."""
        self.message_bar.setConfirmText(text)

    def setCancelText(self, text: str) -> None:
        """Set the text of the prompt cancel button."""
        self.message_bar.setCancelText(text)

    def displayPrompt(self, message: str, is_warning: bool = False) -> None:
        """Display the message bar with with confirm and cancel buttons.

        display message in warning style if `is_warning` is True.
        """
        self.message_bar.displayPrompt(message, is_warning)
