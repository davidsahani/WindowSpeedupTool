from typing import Callable, Generator

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QHeaderView, QStackedWidget, QTableView,
                             QVBoxLayout, QWidget)

from utils import service
from widgets.overlay import MessageOverlay
from widgets.table import CheckableHeaderView, Model


class ServicesView(QTableView):
    def __init__(self, parent: QWidget, services: dict[str, str],
                 show_curr_startup_type: bool = True) -> None:
        super().__init__(parent)
        self.services = services
        self.show_curr_startup_type = show_curr_startup_type
        self.setupTable()

    def setupTable(self) -> None:
        services_list: list[list[str]] = []

        for service_name, startup_type in self.services.items():
            if self.show_curr_startup_type:
                startup_type = service.startup_type(service_name)
            info = service.info(service_name)
            services_list.append([
                service_name,
                info['display_name'],
                info['status'],
                startup_type,
                info['username'],
                info['description']
            ])
        header_names = ["Service Name", "Display Name", "Status",
                        "Startup Type", "User", "Description"]

        self.setModel(Model(self, services_list, header_names))
        # Set column resizing
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Custom)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)

        self.header = CheckableHeaderView(self, all_checked=True)
        self.setVerticalHeader(self.header)
        self.services_list = services_list

    def selectedItems(self) -> Generator[list[str], None, None]:
        """yield the selected items from model"""
        for index, state in enumerate(self.header.check_states):
            if not state:
                continue  # unselected items
            yield self.services_list[index]


# *================================================
# *      SERVICE ACTION CONFIRMATION WIDGET       *
# *================================================


class ConfirmServiceAction(QWidget):
    def __init__(self, master: QWidget, parent: QStackedWidget, services: dict[str, str],
                 show_curr_startup_type: bool = True) -> None:
        super().__init__(parent)
        self._master = master
        self._parent = parent
        self.services = services
        self.show_curr_startup_type = show_curr_startup_type
        self.__function = None
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
        """Setup the widgets in the layout"""
        self.services_view = ServicesView(
            self, self.services, self.show_curr_startup_type)

        message_overlay = MessageOverlay(self, False)
        message_overlay.connect(self.onConfirm)
        message_overlay.connectCancel(self.switchToMaster)
        message_overlay.connectClose(self.switchToMaster)
        self.message_overlay = message_overlay

        layout = QVBoxLayout()
        layout.addWidget(self.services_view)
        layout.addWidget(message_overlay)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setAlignment(message_overlay, Qt.AlignmentFlag.AlignBottom)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def onConfirm(self) -> None:
        """Handle confirm button press event"""
        function = self.__function
        if function is None:
            return
        services_names = (name for name, *_,
                          in self.services_view.selectedItems())
        services = {name: self.services[name] for name in services_names}
        function(services)  # pass in selected services from model
        self.switchToMaster()  # switch to master after confirmation

    def connect(self, function: Callable[[dict[str, str]], None]) -> None:
        """Connect the function to prompt confirm button press event

        Receive:
            selected services
        """
        self.__function = function

    def setConfirmText(self, text: str) -> None:
        """Set the text of the prompt confirm button"""
        self.message_overlay.setConfirmText(text)

    def setCancelText(self, text: str) -> None:
        """Set the text of the prompt cancel button"""
        self.message_overlay.setCancelText(text)

    def displayMessage(self, message: str, is_warning: bool = False) -> None:
        """Display the message overlay with close button.

        display message in warning style if `is_warning` is set to True.
        """
        self.message_overlay.displayMessage(message, is_warning)

    def displayPrompt(self, message: str, is_warning: bool = False) -> None:
        """Display the message prompt overlay.

        display message in warning style if `is_warning` is set to True.
        """
        self.message_overlay.displayPrompt(message, is_warning)


class ErrorWindow(QWidget):
    def __init__(self, services: dict[str, str], show_curr_startup_type: bool = True) -> None:
        super().__init__()
        self.services = services
        self.show_curr_startup_type = show_curr_startup_type
        self.setupWidgets()
        self.resize(950, 600)
        self.setWindowTitle("Failed Services")
        self.show()

    def setupWidgets(self) -> None:
        """Setup the widgets in the layout"""
        services_view = ServicesView(
            self, self.services, self.show_curr_startup_type)

        message_overlay = MessageOverlay(self, False)
        message_overlay.connectClose(self.destroy)
        self.message_overlay = message_overlay

        layout = QVBoxLayout()
        layout.addWidget(services_view)
        layout.addWidget(message_overlay)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setAlignment(message_overlay, Qt.AlignmentFlag.AlignBottom)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def displayMessage(self, message: str, is_warning: bool = False) -> None:
        """Display the message overlay with close button.

        display message in warning style if `is_warning` is set to True.
        """
        self.message_overlay.displayMessage(message, is_warning)
