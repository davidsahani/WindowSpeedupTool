from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QCommandLinkButton, QFrame, QGridLayout,
                             QGroupBox, QProgressBar, QPushButton, QSizePolicy,
                             QSpacerItem, QStackedWidget, QVBoxLayout, QWidget)

import styles
from src.overlay import MessageOverlay
from utils import config, power, service
from windowservices.base_service import Action, BaseService

from .packages_uninstall import PackagesUninstall


def filter_services(services: dict[str, str]) -> dict[str, str]:
    "Filter services from running services."

    running_services = [service_name for service_name, *_ in service.running()]
    return {service_name: startup_type for service_name, startup_type
            in services.items() if service_name in running_services}


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


class AdvanceServices(BaseService):
    def setupWidgets(self) -> None:
        super().setupWidgets()
        self.disable_running_button = QPushButton(
            "Disable Running Services")
        self.enable_unstoppable_services = QPushButton(
            "Enable unstoppable Services")
        self.disable_unstoppable_services = QPushButton(
            "Disable unstoppable Services")
        self.terminate_unstoppable_services = QPushButton(
            "Terminate unstoppable services")
        self.start_necessary_services = QPushButton(
            "Start Necessary Services")
        self.grid.addWidget(self.disable_running_button, 2, 0)
        self.grid.addWidget(self.enable_unstoppable_services, 2, 1)
        self.grid.addWidget(self.disable_unstoppable_services, 3, 0)
        self.grid.addWidget(self.terminate_unstoppable_services, 3, 1)
        self.grid.addWidget(self.start_necessary_services, 4, 0, 4, 2)

    def connectSlots(self) -> None:
        super().connectSlots()
        self.disable_running_button.clicked.connect(  # type: ignore
            self.openDisableRunningServices)
        self.enable_unstoppable_services.clicked.connect(  # type: ignore
            self.openEnableUnstoppableServices)
        self.disable_unstoppable_services.clicked.connect(  # type: ignore
            self.openDisableUnstoppableServices)
        self.terminate_unstoppable_services.clicked.connect(  # type: ignore
            self.openTerminateUnstoppableServices)
        self.start_necessary_services.clicked.connect(  # type: ignore
            self.openStartNecessaryServices)

    def openDisableRunningServices(self) -> None:
        """Open confirm prompt widget to disable running services"""
        services = config.load(self.config_name)
        services = filter_services(services)
        if services:
            self.fireAction(Action.DISABLE, services)
            return
        self.message_overlay.displayMessage("No services running to disable")

    def openEnableUnstoppableServices(self) -> None:
        """Open confirm prompt widget to enable unstoppable services"""
        services = config.load(config.UNSTOPPABLE_SERVICES)
        self.fireAction(Action.ENABLE, services)

    def openDisableUnstoppableServices(self) -> None:
        """Open confirm prompt widget to disable unstoppable services"""
        services = config.load(config.UNSTOPPABLE_SERVICES)
        self.fireAction(Action.DISABLE, services)

    def openStartNecessaryServices(self) -> None:
        """Open confirm prompt widget to start necessary services"""
        services = config.load(config.NECESSARY_SERVICES)
        self.fireAction(Action.START, services)

    def openTerminateUnstoppableServices(self) -> None:
        """Open confirm prompt widget to kill unstoppable services"""
        services = config.load(config.UNSTOPPABLE_SERVICES)
        widget = self.openConfirmationWidget(services)
        widget.displayPrompt("Do you want to terminate these services?")
        widget.setConfirmText("Terminate")
        widget.connect(self.terminateUnstoppableServices)

    def terminateUnstoppableServices(self, services: dict[str, str]) -> None:
        """kill unstoppable services"""
        for service_name in services:
            service.kill(service_name)


class ExtraServices(QGroupBox):
    def __init__(self, parent: QWidget, config_name: str, message_overlay: MessageOverlay) -> None:
        super().__init__(parent)
        self.config_name = config_name
        self.message_overlay = message_overlay
        self.setupWidgets()

    def setupWidgets(self) -> None:
        """Make the widgets and setup the layout"""
        layout = QGridLayout()

        for row, (service_name, _) in enumerate(config.load(self.config_name)):
            display_name = service.display_name(service_name)
            enable_button = QPushButton(f"Enable {display_name}")
            disable_button = QPushButton(f"Disable {display_name}")

            enable_button.clicked.connect(  # type: ignore
                lambda _, x=service_name: self.enableService(x))  # type: ignore
            disable_button.clicked.connect(  # type: ignore
                lambda _, x=service_name: self.disableService(x))  # type: ignore

            layout.addWidget(enable_button, row, 0)
            layout.addWidget(disable_button, row, 1)

        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)

    def enableService(self, service_name: str) -> None:
        """Enable the windows service"""
        services_config = config.load(self.config_name)
        startup_type = services_config[service_name]

        is_warning: bool = False
        if service.info(service_name)['start_type'] != 'disabled':
            message = f"{service_name!r} is already enabled"
        elif not service.set_startup_type(service_name, startup_type):
            message = f"successively enabled: {service_name}"
        else:
            is_warning = True
            message = f"Failed to enable: {service.display_name(service_name)}"

        self.message_overlay.displayMessage(message, is_warning)

    def disableService(self, service_name: str) -> None:
        """Disable the windows service"""
        # backup the service' current config before disabling
        config.backup([service_name], self.config_name)

        is_warning: bool = False
        if service.info(service_name)['start_type'] == 'disabled':
            message = f"{service_name!r} is already disabled"
        elif not service.set_startup_type(service_name, 'disabled'):
            message = f"successively disabled: {service_name}"
        else:
            is_warning = True
            message = f"Failed to disable: {service.display_name(service_name)}"

        self.message_overlay.displayMessage(message, is_warning)


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
