from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QCommandLinkButton, QFrame, QGridLayout,
                             QProgressBar, QPushButton, QSizePolicy,
                             QSpacerItem, QStackedWidget, QVBoxLayout, QWidget)

import styles
from utils import config, power, service
from widgets.overlay import MessageOverlay
from windowservices.base_service import Action, BaseService
from windowservices.windows_services import AdvanceServices

from .packages_uninstall import PackagesUninstall


class Services(BaseService):
    def enableServices(self, services: dict[str, str]) -> None:
        for value, (service_name, startup_value) in enumerate(services.items(), start=1):
            self.valueChanged.emit(value)  # update progressbar
            if service.startup_value(service_name) != 4:
                continue  # don't touch already enabled service
            if not service.set_startup_value(service_name, int(startup_value)):
                continue  # on success
            self._failed_services[service_name] = startup_value

    def disableServices(self, services: dict[str, str]) -> None:
        # backup services' current config before disabling them
        config.backup_reg(services, self.config_name)

        for value, (service_name, startup_value) in enumerate(services.items(), start=1):
            self.valueChanged.emit(value)  # update progressbar
            if service.startup_value(service_name) == 4:
                continue  # don't touch already disabled service
            if not service.set_startup_value(service_name, 4):
                continue  # on success
            self._failed_services[service_name] = startup_value

    def handleFailedServices(self, action: Action) -> None:
        if not self._failed_services and action in [Action.ENABLE, Action.DISABLE]:
            self.promptRestart()
            return  # on success
        super().handleFailedServices(action)

    def promptRestart(self) -> None:
        """Prompt the user to restart the system"""
        self.message_overlay.setConfirmText("Restart")
        msg = "These service changes require restart, Restart Now?"
        self.message_overlay.displayPrompt(msg)
        self.message_overlay.connect(power.restart)


class WindowsDefender(BaseService):
    def setupWidgets(self) -> None:
        self.enable_button = QPushButton("Enable Service")
        self.disable_button = QPushButton("Disable Service")

        layout = QGridLayout()
        layout.addWidget(self.enable_button, 1, 0)
        layout.addWidget(self.disable_button, 1, 1)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)

    def connectSlots(self) -> None:
        self.enable_button.clicked.connect(  # type: ignore
            lambda: self.fireAction(Action.ENABLE))
        self.disable_button.clicked.connect(  # type: ignore
            lambda: self.fireAction(Action.DISABLE))

    def fireAction(self, action: Action, services: dict[str, str] | None = None) -> None:
        services = {
            "WinDefend": "3"
        }
        match action:
            case Action.START:
                self.runServices(services, action)
            case Action.STOP:
                self.runServices(services, action)
            case Action.ENABLE:
                self.runServices(services, action)
            case Action.DISABLE:
                self.runServices(services, action)

    def enableServices(self, services: dict[str, str]) -> None:
        """Enable the windows services"""
        for value, (service_name, startup_value) in enumerate(services.items(), start=1):
            self.valueChanged.emit(value)  # update progressbar
            if service.startup_value(service_name) != 4:
                continue  # don't touch already enabled service
            if not service.set_startup_value(service_name, int(startup_value)):
                continue  # on success
            self._failed_services[service_name] = startup_value

    def disableServices(self, services: dict[str, str]) -> None:
        """Disable the windows services"""
        for value, (service_name, startup_value) in enumerate(services.items(), start=1):
            self.valueChanged.emit(value)  # update progressbar
            if service.startup_value(service_name) == 4:
                continue  # don't touch already disabled service
            if not service.set_startup_value(service_name, 4):
                continue  # on success
            self._failed_services[service_name] = startup_value

    def handleFailedServices(self, action: Action) -> None:
        """Handle failed services and show error message accordingly"""
        is_success = not self._failed_services
        is_warning = False

        match action:
            case Action.ENABLE:
                if is_success:
                    msg = "Successively enabled windows defender"
                else:
                    msg = "Failed to enable windows defender"
                    is_warning = True
            case Action.DISABLE:
                if is_success:
                    msg = "Successively disabled windows defender"
                else:
                    is_warning = True
                    msg = "Failed to disable windows defender"
            case _:
                raise ValueError(f"Invalid action parameter: {action}")
        self.message_overlay.displayMessage(msg, is_warning)


# *================================================
# *              ADVANCE OPTIONS                  *
# *================================================


class AdvanceOptions(QFrame):
    def __init__(self, parent: QStackedWidget) -> None:
        super().__init__(parent)
        self._parent = parent
        self.setupWidgets()
        self.setStyleSheet(styles.get("services"))
        self.packages_uninstall = None

    def setupWidgets(self) -> None:
        """Setup the widgets in layout"""
        self.message_overlay = MessageOverlay(self)
        self.progressbar = QProgressBar(self)
        self.progressbar.setVisible(False)  # hide initially

        advance_services = AdvanceServices(
            self, self._parent, config.ADVANCE_SERVICES,
            self.message_overlay, self.progressbar)
        advance_services.setTitle("Advanced Services")
        advance_services.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        windows_defender = WindowsDefender(
            self, self._parent, config.SECURITY_SERVICES,
            self.message_overlay, self.progressbar)
        windows_defender.setTitle("Windows Defender")
        windows_defender.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        uninstall_packages_button = QCommandLinkButton("Uninstall Packages")
        uninstall_packages_button.setMaximumWidth(355)
        uninstall_packages_button.clicked.connect(  # type:ignore
            self.openPackagesUninstall)

        layout = QVBoxLayout()
        layout.addWidget(self.makeWidget())
        layout.addWidget(advance_services)
        layout.addWidget(windows_defender)
        layout.addWidget(uninstall_packages_button)
        vertical_spacer = QSpacerItem(
            20, 20, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        layout.addSpacerItem(vertical_spacer)
        layout.addWidget(self.progressbar)
        layout.addWidget(self.message_overlay)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def makeWidget(self) -> QWidget:
        """Make widget for security, network, advancex services"""
        security_services = Services(
            self, self._parent, config.SECURITY_SERVICES,
            self.message_overlay, self.progressbar)
        network_services = Services(
            self, self._parent, config.NETWORK_SERVICES,
            self.message_overlay, self.progressbar)
        advancedx_services = Services(
            self, self._parent, config.ADVANCEX_SERVICES,
            self.message_overlay, self.progressbar)
        wlan_services = Services(
            self, self._parent, config.WLAN_SERVICES, self.message_overlay, self.progressbar)

        security_services.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        network_services.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        advancedx_services.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        wlan_services.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        security_services.setTitle("Security Services")
        network_services.setTitle("Network Services")
        advancedx_services.setTitle("AdvancedX Services")
        wlan_services.setTitle("Wlan services")

        widget = QWidget(self)
        layout = QGridLayout(widget)
        layout.addWidget(security_services, 0, 0)
        layout.addWidget(network_services, 0, 1)
        layout.addWidget(advancedx_services, 1, 0)
        layout.addWidget(wlan_services, 1, 1)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)
        return widget

    def openPackagesUninstall(self) -> None:
        """Open Packages-uninstall widget"""
        if self.packages_uninstall is not None:
            self._parent.setCurrentWidget(self.packages_uninstall)
            return
        self.packages_uninstall = PackagesUninstall(self._parent)
        self._parent.addWidget(self.packages_uninstall)
        self._parent.setCurrentWidget(self.packages_uninstall)
