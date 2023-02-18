from enum import Enum
from typing import Sequence

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QWidget

from src.overlay import MessageOverlay
from src.process_terminal import Thread
from utils import power, service

from .update import (WINDOWS_SERVICES_CONFIG, backup_config,
                     is_automatic_drivers_updates_enabled,
                     is_automatic_updates_enabled, is_updates_active,
                     load_config, set_automatic_drivers_updates,
                     set_automatic_updates)
from .update_gui import UpdateGui


class Action(Enum):
    START = 0
    STOP = 1
    ENABLE = 2
    DISABLE = 3
    Active = 4


class WindowsUpdate(QFrame):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.service_names = list(load_config(WINDOWS_SERVICES_CONFIG))
        self.setupWidgets()
        self.connectSlots()
        self.setStates()

    def setupWidgets(self) -> None:
        """Setup widgets in layout"""
        self.gui = UpdateGui(self, self.service_names)
        self.message_overlay = MessageOverlay(self)
        self.message_overlay.setConfirmText("Restart")
        self.message_overlay.connect(power.restart)

        layout = QVBoxLayout(self)
        layout.addWidget(self.gui)
        layout.addWidget(self.message_overlay, 1)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setAlignment(self.message_overlay, Qt.AlignmentFlag.AlignBottom)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def setStates(self) -> None:
        """Set widget's current state texts and checks"""
        if is_updates_active(self.service_names):
            self.gui.status_label.setText("Status: Active")
            self.gui.toggle_update_button.setText("Deactivate")
        else:
            self.gui.status_label.setText("Status: Inactive")
            self.gui.toggle_update_button.setText("Activate")

        self.gui.automatic_updates_checkbox.setChecked(
            is_automatic_updates_enabled())
        self.gui.automatic_driver_updates_checkbox.setChecked(
            is_automatic_drivers_updates_enabled())

        for service_name, (status_button, state_button) in self.gui.ins_dict.items():
            is_stopped = service.status(service_name)[1] == 1
            is_disabled = service.info(service_name)[
                "start_type"] == "disabled"

            if is_stopped:
                status_button.setText("Start")
            else:
                status_button.setText("Stop")
            if is_disabled:
                state_button.setText("Enable")
            else:
                state_button.setText("Disable")
            if is_disabled:
                status_button.setDisabled(True)
            else:
                status_button.setDisabled(False)

    def connectSlots(self) -> None:
        """Connect buttons' and checkboxes' click events"""
        service_names = self.service_names

        self.gui.toggle_update_button.clicked.connect(  # type: ignore
            lambda: self.fireAction(service_names, Action.Active))

        self.gui.automatic_updates_checkbox.clicked.\
            connect(self.setAutomaticUpdates)  # type: ignore
        self.gui.automatic_driver_updates_checkbox.clicked.\
            connect(self.setAutomaticDriversUpdates)  # type: ignore

        for service_name, (status_button, state_button) in self.gui.ins_dict.items():
            status_button.clicked.connect(  # type: ignore
                lambda _, x=service_name: self.setServiceStatus(x))  # type: ignore
            state_button.clicked.connect(  # type: ignore
                lambda _, x=service_name: self.setServiceState(x))  # type: ignore

        self.gui.start_services_button.clicked.connect(   # type: ignore
            lambda: self.fireAction(service_names, Action.START))
        self.gui.stop_services_button.clicked.connect(   # type: ignore
            lambda: self.fireAction(service_names, Action.STOP))
        self.gui.enable_services_button.clicked.connect(   # type: ignore
            lambda: self.fireAction(service_names, Action.ENABLE))
        self.gui.disable_services_button.clicked.connect(   # type: ignore
            lambda: self.fireAction(service_names, Action.DISABLE))

    def setAutomaticUpdates(self, checked: bool) -> None:
        """Enable windows automatic updates,

        if `checked` is True else Disable
        """
        status = set_automatic_updates(checked)
        if status:
            if checked:
                msg = f"Failed to enable automatic windows update, status code: {status}"
            else:
                msg = f"Failed to disable automatic windows update, status code: {status}"
            self.message_overlay.displayMessage(msg, True)
        else:
            if checked:
                msg = "Enabled automatic windows update"
            else:
                msg = "Disabled automatic windows update"
            self.message_overlay.displayPrompt(
                msg + ", restart to confirm changes?")

    def setAutomaticDriversUpdates(self, checked: bool) -> None:
        """Enable automatic drivers updates on windows update,

        if `checked` is True else Disable
        """
        status = set_automatic_drivers_updates(checked)
        if status:
            if checked:
                msg = f"Failed to enable automatic drivers update, status code: {status}"
            else:
                msg = f"Failed to disable automatic drivers update, status code: {status}"
            self.message_overlay.displayMessage(msg, True)
        else:
            if checked:
                msg = "Enabled automatic drivers update"
            else:
                msg = "Disabled automatic drivers update"
            self.message_overlay.displayPrompt(
                msg + ", restart to confirm changes?")

    def setServiceStatus(self, service_name: str) -> None:
        """Start/Stop service"""
        status_button, _ = self.gui.ins_dict[service_name]
        if status_button.text() == "Start":
            self.fireAction([service_name], Action.START)
        else:
            self.fireAction([service_name], Action.STOP)

    def setServiceState(self, service_name: str) -> None:
        """Enable/Disabled service"""
        _, state_button = self.gui.ins_dict[service_name]
        if state_button.text() == "Enable":
            self.fireAction([service_name], Action.ENABLE)
        else:
            self.fireAction([service_name], Action.DISABLE)

    def fireAction(self, service_names: Sequence[str], action: Action) -> None:
        """Start the corresponding actions"""
        match action:
            case Action.START:
                self.__start_failed_services: list[str] = []
                self.__start_thread = Thread(self.startServices, service_names)
                self.__start_thread.start()
                self.__start_thread.finished.connect(  # type: ignore
                    lambda: self.onStartThreadFinish(service_names)
                )
                msg = "Starting"
            case Action.STOP:
                self.__stop_failed_services: list[str] = []
                self.__stop_thread = Thread(self.stopServices, service_names)
                self.__stop_thread.start()
                self.__stop_thread.finished.connect(  # type: ignore
                    lambda: self.onStopThreadFinish(service_names)
                )
                msg = "Stopping"
            case Action.ENABLE:
                self.__prompt_restart = False
                self.__enable_failed_services: list[str] = []
                self.__enable_thread = Thread(
                    self.enableServices, service_names)
                self.__enable_thread.start()
                self.__enable_thread.finished.connect(  # type: ignore
                    lambda: self.onEnableThreadFinish(service_names)
                )
                msg = "Enabling"
            case Action.DISABLE:
                self.__prompt_restart = False
                self.__disable_failed_services: list[str] = []
                self.__disable_thread = Thread(
                    self.disableServices, service_names)
                self.__disable_thread.start()
                self.__disable_thread.finished.connect(  # type: ignore
                    lambda: self.onDisableThreadFinish(service_names)
                )
                msg = "Disabling"
            case Action.Active:
                if self.gui.toggle_update_button.text() == "Activate":
                    self.fireAction(service_names, Action.ENABLE)
                    thread = self.__enable_thread
                    failed_services = self.__enable_failed_services
                else:
                    self.fireAction(service_names, Action.STOP)
                    self.fireAction(service_names, Action.DISABLE)
                    thread = self.__disable_thread
                    failed_services = self.__disable_failed_services

                self.__thread = Thread(
                    self.updateActiveButton, thread, failed_services)
                self.__thread.start()
                msg = ""
            case _:
                msg = ""  # to avoid variable unbound linter warning
                raise ValueError(f"Invalid action parameter: {action}")
        if not msg:
            return
        if len(service_names) != 1:
            msg += " services..."
        else:
            msg += " service: %s" % service.display_name(service_names[0])
        self.message_overlay.displayMessage(msg)

    def updateActiveButton(self, thread: Thread, failed_services: list[str]) -> None:
        """Update Active button text"""
        thread.wait()
        if failed_services:
            return  # no change on failure

        if self.gui.toggle_update_button.text() == "Activate":
            self.gui.toggle_update_button.setText("Deactivate")
        else:
            self.gui.toggle_update_button.setText("Activate")

    def startServices(self, service_names: Sequence[str]) -> None:
        """Start the windows services"""
        for service_name in service_names:
            if service.status(service_name)[1] == 4:
                continue  # if already running
            if not service.start(service_name):
                continue    # on success
            if not service.net_start(service_name):
                continue    # on success
            self.__start_failed_services.append(service_name)

    def stopServices(self, service_names: Sequence[str]) -> None:
        """Stop the windows services"""
        for service_name in service_names:
            if service.status(service_name)[1] == 1:
                continue  # if already stopped
            if not service.stop(service_name):
                continue  # on success
            if not service.net_stop(service_name):
                continue  # on success
            self.__stop_failed_services.append(service_name)

    def enableServices(self, service_names: Sequence[str]) -> None:
        """Enable the windows services"""
        services_config = load_config(WINDOWS_SERVICES_CONFIG)

        for service_name in service_names:
            if service.info(service_name)['start_type'] != 'disabled':
                continue  # don't touch already enabled service
            startup_type, startup_value = services_config[service_name]
            if not service.set_startup_type(service_name, startup_type):
                continue  # on success
            if not service.set_startup_value(service_name, int(startup_value)):
                self.__prompt_restart = True
                continue  # on success
            self.__enable_failed_services.append(service_name)

    def disableServices(self, service_names: Sequence[str]) -> None:
        """Disable the windows services"""
        # backup the services' current config before disabling them
        backup_config(service_names, WINDOWS_SERVICES_CONFIG)

        for service_name in service_names:
            if service.info(service_name)['start_type'] == 'disabled':
                continue  # don't touch already disabled service
            if not service.set_startup_type(service_name, 'disabled'):
                continue  # on success
            if not service.set_startup_value(service_name, 4):
                self.__prompt_restart = True
                continue  # on success
            self.__disable_failed_services.append(service_name)

    def onStartThreadFinish(self, service_names: Sequence[str]) -> None:
        """Display start success/failure message,

        update status button text on success.
        """
        if self.__start_failed_services:
            failed_services = tuple(
                map(service.display_name, self.__start_failed_services))
            if len(failed_services) == 1:
                msg = f"Failed to start service: {failed_services[0]}"
            else:
                msg = f"Failed to start services: {failed_services}"
            self.message_overlay.displayMessage(msg, True)
            return

        if len(service_names) != 1:
            msg = "Successively started services"
        else:
            msg = "Successively started service: " +\
                service.display_name(service_names[0])
        self.message_overlay.displayMessage(msg)

        for service_name in service_names:
            if service_name in self.__start_failed_services:
                continue  # skip failed services
            status_button, _ = self.gui.ins_dict[service_names[0]]
            status_button.setText("Stop")

    def onStopThreadFinish(self, service_names: Sequence[str]) -> None:
        """Display stop success/failure message,

        update status button text on success.
        """
        if self.__stop_failed_services:
            failed_services = tuple(
                map(service.display_name, self.__stop_failed_services))
            if len(failed_services) == 1:
                msg = f"Failed to stop service: {failed_services[0]}"
            else:
                msg = f"Failed to stop services: {failed_services}"
            self.message_overlay.displayMessage(msg, True)
            return

        if len(service_names) != 1:
            msg = "Successively stopped services"
        else:
            msg = "Successively stopped service: " +\
                service.display_name(service_names[0])
        self.message_overlay.displayMessage(msg, False)

        for service_name in service_names:
            if service_name in self.__stop_failed_services:
                continue  # skip failed services
            status_button, state_button = self.gui.ins_dict[service_names[0]]
            status_button.setText("Start")
            if state_button.text() == "Enable":
                status_button.setDisabled(True)

    def onEnableThreadFinish(self, service_names: Sequence[str]) -> None:
        """Display enable success/failure message,

        update status and state buttons,
        and prompt restart if required.
        """
        if self.__enable_failed_services:
            failed_services = tuple(
                map(service.display_name, self.__enable_failed_services))
            if len(failed_services) == 1:
                msg = f"Failed to enable service: {failed_services[0]}"
            else:
                msg = f"Failed to enable services: {failed_services}"
            self.message_overlay.displayMessage(msg, True)
            return

        if len(service_names) != 1:
            msg = "Successively enabled services"
        else:
            msg = "Successively enabled service: " +\
                service.display_name(service_names[0])
        if self.__prompt_restart:
            self.promptRestart()
        else:
            self.message_overlay.displayMessage(msg)

        for service_name in service_names:
            if service_name in self.__enable_failed_services:
                continue  # skip failed services
            status_button, state_button = self.gui.ins_dict[service_name]
            status_button.setEnabled(True)
            state_button.setText("Disable")

    def onDisableThreadFinish(self, service_names: Sequence[str]) -> None:
        """Display disable success/failure message,

        update status and state buttons,
        and prompt restart if required.
        """
        if self.__disable_failed_services:
            failed_services = tuple(
                map(service.display_name, self.__disable_failed_services))
            if len(failed_services) == 1:
                msg = f"Failed to disable service: {failed_services[0]}"
            else:
                msg = f"Failed to disable services: {failed_services}"
            self.message_overlay.displayMessage(msg, True)
            return

        if len(service_names) != 1:
            msg = "Successively disabled services"
        else:
            msg = "Successively disabled service: " +\
                service.display_name(service_names[0])
        if self.__prompt_restart:
            self.promptRestart()
        else:
            self.message_overlay.displayMessage(msg)

        for service_name in service_names:
            if service_name in self.__disable_failed_services:
                continue  # skip failed services
            status_button, state_button = self.gui.ins_dict[service_name]
            if service.status(service_names[0])[1] == 1:
                status_button.setDisabled(True)
            state_button.setText("Enable")

    def promptRestart(self) -> None:
        """Prompt the user to restart the system"""
        self.message_overlay.setConfirmText("Restart")
        msg = "These changes require restart, Restart Now?"
        self.message_overlay.displayPrompt(msg)
