from typing import override

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QCommandLinkButton, QVBoxLayout, QWidget

from utils import config
from widgets.stacked_widget import StackedWidget
from windows_services.windows_services import Action, WindowsServices

from .packages_uninstall import PackagesUninstall


class AdvanceOptions(WindowsServices):
    def __init__(self, parent: StackedWidget) -> None:
        super().__init__(parent)
        self.packages_uninstall = None

    @override
    def setupWidgets(self) -> None:
        super().setupWidgets()

        uninstall_packages_button = QCommandLinkButton("Uninstall Packages")
        uninstall_packages_button.clicked.connect(self.openPackagesUninstall)

        layout = QVBoxLayout()
        layout.addWidget(uninstall_packages_button)
        layout.setContentsMargins(0, 0, 0, 6)

        self._layout.addLayout(
            layout, 1, 0,
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft
        )

    @override
    def createMainWidget(self) -> QWidget:
        self.config = config.load()
        return self.createServicesWidget(self.config.advance_services)

    @override
    def revert(self) -> None:
        services = self.getBackedUpServices(self.config.advance_services)
        if services is None:
            return
        if services:
            self.fireAction(Action.DISABLE, services)
        else:
            self.message_bar.displayMessage(
                "No advanced backed-up services found to disable."
            )

    @override
    def restore(self) -> None:
        services = self.getBackedUpServices(self.config.advance_services)
        if services is None:
            return
        if services:
            self.fireAction(Action.ENABLE, services)
        else:
            self.message_bar.displayMessage(
                "No advanced backed-up services found to enable."
            )

    def openPackagesUninstall(self) -> None:
        """Open Packages-uninstall widget."""
        if self.packages_uninstall is not None:
            self._parent.setCurrentWidget(self.packages_uninstall)
            return
        self.packages_uninstall = PackagesUninstall(self._parent)
        self._parent.addWidget(self.packages_uninstall)
        self._parent.setCurrentWidget(self.packages_uninstall)
