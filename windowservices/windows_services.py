from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QFrame, QGridLayout, QGroupBox, QProgressBar,
                             QPushButton, QSizePolicy, QSpacerItem,
                             QStackedWidget, QVBoxLayout, QWidget)

import styles
from utils import config, power, service
from widgets.overlay import MessageOverlay

from .base_service import Action, BaseService
from .normal_specific_services import NormalSpecificServices


def filter_services(services: dict[str, str]) -> dict[str, str]:
    "Filter services from running services."

    running_services = [service_name for service_name, *_ in service.running()]
    return {service_name: startup_type for service_name, startup_type
            in services.items() if service_name in running_services}


class NormalServices(BaseService):
    def setupWidgets(self) -> None:
        super().setupWidgets()
        self.disable_running_button = QPushButton(
            "Disable Running Services")
        self.grid.addWidget(self.disable_running_button, 2, 0, 2, 2)
        self.disable_running_button.clicked.connect(  # type: ignore
            self.openDisableRunningServices)

    def openDisableRunningServices(self) -> None:
        """Open confirm prompt widget to disable running services"""
        services = config.load(self.config_name)
        services = filter_services(services)
        if services:
            self.fireAction(Action.DISABLE, services)
            return
        self.message_overlay.displayMessage("No services running to disable")


class HiddenServices(BaseService):
    def setupWidgets(self) -> None:
        super().setupWidgets()
        self.stop_all_services = QPushButton(
            "Stop All Hidden Running Services")
        self.grid.addWidget(self.stop_all_services, 2, 0, 2, 2)

    def connectSlots(self) -> None:
        super().connectSlots()
        self.stop_all_services.clicked.connect(  # type: ignore
            self.openStopAllServices)

    def openStopAllServices(self) -> None:
        """Open confirm prompt widget to stop all hidden services"""
        hidden_services = [svc_name for svc_name, *_,
                           in service.running() if '_' in svc_name]
        services = {svc_name: service.startup_type(svc_name)
                    for svc_name in hidden_services}
        if services:
            self.fireAction(Action.STOP, services)
            return
        self.message_overlay.displayMessage("No services running to stop")

    def enableServices(self, services: dict[str, str]) -> None:
        for service_name, start_value in services.items():
            if service.startup_value(service_name) != 4:
                continue  # don't touch already enabled service
            if not service.set_startup_value(service_name, int(start_value)):
                continue  # on success
            self._failed_services[service_name] = start_value

    def disableServices(self, services: dict[str, str]) -> None:
        # backup services' current config before disabling them
        config.backup_reg(services, self.config_name)

        for service_name, start_value in services.items():
            if service.startup_value(service_name) == 4:
                continue  # don't touch already disable service
            if not service.set_startup_value(service_name, 4):
                continue  # on success
            self._failed_services[service_name] = start_value

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

        for row, service_name in enumerate(config.load(self.config_name)):
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
        # backup service' current config before disabling
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


# *================================================
# *              WINDOWS SERVICES                 *
# *================================================


class WindowServices(QFrame):
    def __init__(self, parent: QStackedWidget) -> None:
        super().__init__(parent)
        self._parent = parent
        self.setupWidgets()
        self.setStyleSheet(styles.get("services"))

    def setupWidgets(self) -> None:
        """Setup the widgets in layout"""
        self.message_overlay = MessageOverlay(self)
        self.progressbar = QProgressBar(self)
        self.progressbar.hide()  # hide initially

        advanced_services = AdvanceServices(
            self, self._parent, config.ADVANCE_SERVICES,
            self.message_overlay, self.progressbar)
        advanced_services.setTitle("Advance Services")
        advanced_services.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout()
        layout.addWidget(self.makeWidget())
        layout.addWidget(advanced_services)
        vertical_spacer = QSpacerItem(
            20, 20, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        layout.addSpacerItem(vertical_spacer)
        layout.addWidget(self.progressbar)
        layout.addWidget(self.message_overlay)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def makeWidget(self) -> QWidget:
        """Make a widget for laptop, desktop, hidden and extra services"""
        laptop_services = NormalServices(
            self, self._parent, config.LAPTOP_SERVICES,
            self.message_overlay, self.progressbar)
        normal_services = NormalServices(
            self, self._parent, config.NORMAL_SERVICES,
            self.message_overlay, self.progressbar)
        hidden_services = HiddenServices(
            self, self._parent, config.HIDDEN_SERVICES,
            self.message_overlay, self.progressbar)
        extra_services = ExtraServices(
            self, config.EXTRA_SERVICES, self.message_overlay)

        laptop_services.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        normal_services.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        hidden_services.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        extra_services.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

        laptop_services.setTitle("Laptop Services")
        normal_services.setTitle("Desktop Services")
        hidden_services.setTitle("Hidden Services")
        extra_services.setTitle("Extra Services")

        button = QPushButton("Manage Normal Specific Services")
        button.clicked.connect(  # type: ignore
            lambda: NormalSpecificServices(
                self, self._parent, config.NORMAL_SPECIFIC, config.NORMAL_SERVICES)
        )
        widget = QWidget(self)
        layout = QGridLayout(widget)
        layout.addWidget(laptop_services, 0, 0)
        layout.addWidget(normal_services, 0, 1)
        layout.addWidget(button, 1, 0)
        layout.addWidget(extra_services, 2, 0)
        layout.addWidget(hidden_services, 2, 1)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)
        return widget
