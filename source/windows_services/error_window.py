from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHeaderView, QTableView, QVBoxLayout, QWidget

from utils import service
from widgets.message_bar import MessageBar
from widgets.table import TableModel

from .services_thread import FailedServicesType


class ErrorsView(QTableView):
    def __init__(self, parent: QWidget, services: FailedServicesType,
                 show_curr_startup_type: bool) -> None:
        super().__init__(parent)
        self.services = services
        self.show_curr_startup_type = show_curr_startup_type
        self.setupTable()

    def setupTable(self) -> None:
        services_list: list[list[str]] = []

        for svc, error in self.services:
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
                error
            ])

        header_names = ["Service Name", "Display Name", "Status",
                        "Startup Type", "User", "Error"]

        self.setModel(TableModel(services_list, header_names))
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


class ErrorWindow(QWidget):
    def __init__(self, services: FailedServicesType, show_curr_startup_type: bool = True) -> None:
        super().__init__()
        self.services = services
        self.show_curr_startup_type = show_curr_startup_type
        self.setupWidgets()
        self.resize(950, 600)
        self.setWindowTitle("Failed Services")
        self.show()

    def setupWidgets(self) -> None:
        """Setup the widgets in layout."""
        errors_view = ErrorsView(
            self, self.services, self.show_curr_startup_type
        )
        self.message_bar = MessageBar(False)
        self.message_bar.connectClose(self.destroy)

        layout = QVBoxLayout()
        layout.addWidget(errors_view)
        layout.addWidget(self.message_bar)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setAlignment(self.message_bar, Qt.AlignmentFlag.AlignBottom)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def displayMessage(self, message: str, is_warning: bool = False) -> None:
        """Display the message bar with close button.

        display message in warning style if `is_warning` is True.
        """
        self.message_bar.displayMessage(message, is_warning)
