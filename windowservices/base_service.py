from enum import Enum

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QGridLayout, QGroupBox, QProgressBar, QPushButton,
                             QStackedWidget, QWidget)

from utils import config, service
from widgets.overlay import MessageOverlay
from widgets.process_terminal import Thread

from .confirm_action import ConfirmServiceAction, ErrorWindow


class Action(Enum):
    START = 0
    STOP = 1
    ENABLE = 2
    DISABLE = 3


class BaseService(QGroupBox):
    valueChanged = pyqtSignal(int)

    def __init__(self, parent: QWidget, stacked_widget: QStackedWidget, config_name: str,
                 message_overlay: MessageOverlay, progressbar: QProgressBar) -> None:
        super().__init__(parent)
        self._parent = parent
        self.config_name = config_name
        self.stacked_widget = stacked_widget
        self.message_overlay = message_overlay
        self.progressbar = progressbar
        self.setupWidgets()
        self.connectSlots()

    def setupWidgets(self) -> None:
        """Setup the widgets in layout"""
        self.start_button = QPushButton("Start Services")
        self.stop_button = QPushButton("Stop Services")
        self.enable_button = QPushButton("Enable Services")
        self.disable_button = QPushButton("Disable Services")

        layout = QGridLayout()
        layout.addWidget(self.start_button, 0, 0)
        layout.addWidget(self.stop_button, 0, 1)
        layout.addWidget(self.enable_button, 1, 0)
        layout.addWidget(self.disable_button, 1, 1)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)
        self.grid = layout

    def connectSlots(self) -> None:
        """Connect the buttons' events to their corresponding actions"""
        self.start_button.clicked.connect(  # type: ignore
            lambda: self.fireAction(Action.START))
        self.stop_button.clicked.connect(  # type: ignore
            lambda: self.fireAction(Action.STOP))
        self.enable_button.clicked.connect(  # type: ignore
            lambda: self.fireAction(Action.ENABLE))
        self.disable_button.clicked.connect(  # type: ignore
            lambda: self.fireAction(Action.DISABLE))

    def openConfirmationWidget(self, services: dict[str, str], show_curr_startup_type: bool = True) \
            -> ConfirmServiceAction:
        """Open the service confirmation widget"""
        return ConfirmServiceAction(self._parent, self.stacked_widget, services, show_curr_startup_type)

    def fireAction(self, action: Action, services: dict[str, str] | None = None) -> None:
        """Open confirmation widget and start the corresponding actions on confirmation"""
        if services is None:
            services = config.load(self.config_name)

        match action:
            case Action.START:
                widget = self.openConfirmationWidget(services)
                widget.displayPrompt("Do you want to start these services?")
                widget.setConfirmText("Start")
                widget.connect(lambda svcs: self.runServices(svcs, action))
            case Action.STOP:
                widget = self.openConfirmationWidget(services)
                widget.displayPrompt("Do you want to stop these services?")
                widget.setConfirmText("Stop")
                widget.connect(lambda svcs: self.runServices(svcs, action))
            case Action.ENABLE:
                widget = self.openConfirmationWidget(
                    services, show_curr_startup_type=False)
                widget.displayPrompt("Do you want to enable these services?")
                widget.setConfirmText("Enable")
                widget.connect(lambda svcs: self.runServices(svcs, action))
            case Action.DISABLE:
                widget = self.openConfirmationWidget(services)
                widget.displayPrompt("Do you want to disable these services?")
                widget.setConfirmText("Disable")
                widget.connect(lambda svcs: self.runServices(svcs, action))
            case _:  # type: ignore
                raise ValueError(f"Invalid action parameter: {action}")

    def runServices(self, services: dict[str, str], action: Action) -> None:
        """Run corresponding services in new thread"""
        match action:
            case Action.START:
                self._disabled_services: dict[str, str] = {}
                self.__thread = Thread(self.startServices, services)
                self.progressbar.setFormat("Starting services: %v/%m (%p%)")
            case Action.STOP:
                self.__thread = Thread(self.stopServices, services)
                self.progressbar.setFormat("Stopping services: %v/%m (%p%)")
            case Action.ENABLE:
                self.__thread = Thread(self.enableServices, services)
                self.progressbar.setFormat("Enabling services: %v/%m (%p%)")
            case Action.DISABLE:
                self.__thread = Thread(self.disableServices, services)
                self.progressbar.setFormat("Disabling services: %v/%m (%p%)")
            case _:  # type: ignore
                raise ValueError(f"Invalid action parameter: {action}")
        self._failed_services: dict[str, str] = {}
        self.__thread.start()
        self.__thread.finished.connect(  # type: ignore
            lambda: self.handleFailedServices(action)
        )
        self.valueChanged.connect(self.updateProgressbar)
        self.progressbar.setRange(0, len(services))
        self.progressbar.show()  # show on progress start
        self.__thread.finished.connect(self.progressbar.hide)  # type: ignore

    def updateProgressbar(self, value: int) -> None:
        """Update the progressbar"""
        self.progressbar.setValue(value)
        if value < self.progressbar.maximum():
            return
        # hide progressbar on finish
        self.progressbar.hide()

    def startServices(self, services: dict[str, str]) -> None:
        """Start the windows services"""
        for value, (service_name, startup_type) in enumerate(services.items(), start=1):
            self.valueChanged.emit(value)  # update progressbar
            if service.status(service_name)[1] == 4:
                continue  # if already running
            if not service.start(service_name):
                continue  # on success
            if service.info(service_name)['start_type'] == 'disabled':
                self._disabled_services[service_name] = startup_type
                continue  # on being disabled
            if not service.net_start(service_name):
                continue  # on success
            self._failed_services[service_name] = startup_type

    def stopServices(self, services: dict[str, str]) -> None:
        """Stop the windows services"""
        for value, (service_name, startup_type) in enumerate(services.items(), start=1):
            self.valueChanged.emit(value)  # update progressbar
            if service.status(service_name)[1] == 1:
                continue  # if already stopped
            if not service.stop(service_name):
                continue  # on success
            if not service.net_stop(service_name):
                continue  # on success
            self._failed_services[service_name] = startup_type

    def enableServices(self, services: dict[str, str]) -> None:
        """Enable the windows services"""
        for value, (service_name, startup_type) in enumerate(services.items(), start=1):
            self.valueChanged.emit(value)  # update progressbar
            if service.info(service_name)['start_type'] != 'disabled':
                continue  # don't touch already enabled service
            if not service.set_startup_type(service_name, startup_type):
                continue  # on success
            self._failed_services[service_name] = startup_type

    def disableServices(self, services: dict[str, str]) -> None:
        """Disable the windows services"""
        # backup services' current config before disabling
        config.backup(services, self.config_name)

        for value, (service_name, startup_type) in enumerate(services.items(), start=1):
            self.valueChanged.emit(value)  # update progressbar
            if service.info(service_name)['start_type'] == 'disabled':
                continue  # don't touch already disabled service
            if not service.set_startup_type(service_name, 'disabled'):
                continue  # on success
            self._failed_services[service_name] = startup_type

    # **************************************************************************
    #                           HANDLE ERRORS                                  *
    # **************************************************************************

    def handleFailedServices(self, action: Action) -> None:
        """Handle failed services and show error message accordingly"""
        services_length = self.progressbar.maximum()
        ratio = f"{len(self._failed_services)}/{services_length}"

        if action == Action.START:
            ratio0 = f"{len(self._disabled_services)}/{services_length}"
            if self._disabled_services and self._failed_services:
                msg = f"{ratio} services failed to start, {ratio0} services are disabled, Enable them?"
                self.promptEnableDisabledServices(msg, self._disabled_services)
            elif self._disabled_services:
                msg = f"{ratio0} services failed to start due to being disabled, Enable them?"
                self.promptEnableDisabledServices(msg, self._disabled_services)

        if not self._failed_services:
            return  # on success

        match action:
            case Action.START:
                msg = f"{ratio} services failed to start, would you like to see them?"
            case Action.STOP:
                msg = f"{ratio} services failed to stop, would you like to see them?"
            case Action.ENABLE:
                msg = f"{ratio} services failed to enable, would you like to see them?"
            case Action.DISABLE:
                msg = f"{ratio} services failed to disable, would you like to see them?"
            case _:  # type: ignore
                raise ValueError(f"Invalid action parameter: {action}")
        self.promptShowFailedServices(self._failed_services, msg, action)

    def promptEnableDisabledServices(self, message: str, services: dict[str, str]) -> None:
        """Prompt user to enable disabled services"""
        self.message_overlay.displayPrompt(message)
        self.message_overlay.setConfirmText("Enable")
        self.message_overlay.connect(self.fireAction, Action.ENABLE, services)

    def promptShowFailedServices(self, services: dict[str, str], message: str, action: Action) -> None:
        """Prompt user to show failed services"""
        self.message_overlay.displayPrompt(message, True)
        self.message_overlay.setConfirmText("Show")
        self.message_overlay.connect(
            self.openFailedServiceWindow, services, action)

    def openFailedServiceWindow(self, services: dict[str, str], action: Action) -> None:
        """Display failed services in a new error window"""
        match action:
            case Action.START:
                msg = "Failed to start these services"
            case Action.STOP:
                msg = "Failed to stop these services"
            case Action.ENABLE:
                msg = "Failed to enable these services"
            case Action.DISABLE:
                msg = "Failed to disable these services"
            case _:  # type: ignore
                raise ValueError(f"Invalid action parameter: {action}")
        self.err_win = ErrorWindow(services)
        self.err_win.displayMessage(msg, True)

    # ? NOT IN USE, might be used later
    def showFailedServices(self, services: dict[str, str], action: Action) -> None:
        """Show failed services in service confirmation widget"""
        match action:
            case Action.START:
                message = "Failed to start these services"
            case Action.STOP:
                message = "Failed to stop these services"
            case Action.ENABLE:
                message = "Failed to enable services"
            case Action.DISABLE:
                message = "Failed to disable services"
            case _:  # type: ignore
                raise ValueError(f"Invalid action parameter: {action}")
        widget = ConfirmServiceAction(
            self._parent, self.stacked_widget, services)
        widget.displayMessage(message, True)
