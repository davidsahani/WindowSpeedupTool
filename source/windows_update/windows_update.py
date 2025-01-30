from collections import deque
from functools import partial

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QGridLayout, QWidget

from utils import config, power, service, styles
from utils.config_parser import Error, Service
from widgets.message_bar import MessageBar
from windows_services.services_thread import (
    Action,
    FailedServicesType,
    ServicesThread,
    ServicesType,
)

from .update import (
    is_any_service_running,
    is_automatic_drivers_updates_enabled,
    is_automatic_updates_enabled,
    set_automatic_drivers_updates,
    set_automatic_updates,
)
from .update_gui import UpdateGui


class WindowsUpdate(QFrame):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setupWidgets()
        self.setMainWidget()
        self.setStyleSheet(styles.get("windows_update"))
        self._action_callbacks: deque[partial[None]] = deque()

    def setupWidgets(self) -> None:
        """Setup the widgets in layout."""
        self.message_bar = MessageBar()

        layout = QGridLayout()
        layout.addWidget(self.message_bar, 1, 0)
        layout.setRowStretch(1, 1)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setAlignment(self.message_bar, Qt.AlignmentFlag.AlignBottom)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self._layout = layout

    def setMainWidget(self) -> None:
        """Set the windows update gui widget."""
        try:
            config_ = config.load()
            self.config_dir = config_.config_dir
            self.backup_dir = config_.backup_dir
            self.filename = config_.update_filename

            self.services = config.load_file(
                self.filename, self.config_dir, self.backup_dir
            )
            self.gui = UpdateGui(self.services)
            self._layout.addWidget(self.gui, 0, 0)

            self.connectSlots()  # setup thread and callbacks.
            self.setStatesAndStatues()  # set services states and statuses.

        except (OSError, Error) as e:
            self.message_bar.message_close.enable_timer = False
            self.message_bar.displayMessage(str(e), True)
            self.message_bar.setRetryStyleForCloseButton(True)
            self.message_bar.message_close.close_button.setText("Reload")
            self.message_bar.connectClose(self.setMainWidget)
        else:
            self.message_bar.connectClose(lambda: None)
            self.message_bar.setRetryStyleForCloseButton(False)
            self.message_bar.message_close.enable_timer = True

    def connectSlots(self) -> None:
        """Connect the callbacks to their corresponding events."""
        self.gui.update_icon_button.clicked.\
            connect(self.setStatesAndStatues)

        self.gui.toggle_update_button.clicked.\
            connect(self.changeWindowsUpdate)

        self.gui.automatic_updates_checkbox.clicked.\
            connect(self.setAutomaticUpdates)
        self.gui.automatic_driver_updates_checkbox.clicked.\
            connect(self.setAutomaticDriversUpdates)

        for service_name, (status_button, state_button) in self.gui.ins_dict.items():
            svc = [svc for svc in self.services
                   if svc.service_name == service_name][0]
            status_button.clicked.connect(
                partial(self.changeServiceStatus, svc))
            state_button.clicked.connect(partial(self.changeServiceState, svc))

        self.gui.start_services_button.clicked.connect(
            lambda: self.runServices(Action.START)
        )
        self.gui.stop_services_button.clicked.connect(
            lambda: self.runServices(Action.STOP)
        )
        self.gui.enable_services_button.clicked.connect(
            lambda: self.runServices(Action.ENABLE)
        )
        self.gui.disable_services_button.clicked.connect(
            lambda: self.runServices(Action.DISABLE)
        )

        self._thread = ServicesThread()
        self._thread.connectFinished(self.handleFinishedServices)
        self._thread.finished.connect(self._processActions)  # process queue.

    def setStatesAndStatues(self) -> None:
        """Set widget's current states, statues and checks."""
        self.updateWindowsUpdateStatus()

        self.gui.automatic_updates_checkbox.setChecked(
            is_automatic_updates_enabled()
        )
        self.gui.automatic_driver_updates_checkbox.setChecked(
            is_automatic_drivers_updates_enabled()
        )

        for service_name, (status_button, state_button) in self.gui.ins_dict.items():
            status_result = service.status(service_name)
            info_result = service.info(service_name)

            if status_result.value is None:
                status_button.setText("Unknown")
            elif status_result.value[1] == 4:  # running
                status_button.setText("Stop")
            else:
                status_button.setText("Start")

            if info_result.value is None:
                state_button.setText("Unknown")
            elif info_result.value["start_type"] == "disabled":
                state_button.setText("Enable")
                status_button.setDisabled(True)
            else:
                state_button.setText("Disable")
                status_button.setDisabled(False)

    def updateWindowsUpdateStatus(self) -> None:
        """Update the status of windows update widgets."""
        result = is_any_service_running(
            (svc.service_name for svc in self.services)
        )
        if result.value is None:
            self.gui.status_label.setText("Status: Unknown")
            self.gui.toggle_update_button.setText("Deactivate")
            self.message_bar.displayMessage(result.error.stderr, True)

        elif result.value:
            self.gui.status_label.setText("Status: Active")
            self.gui.toggle_update_button.setText("Deactivate")
        else:
            self.gui.status_label.setText("Status: Inactive")
            self.gui.toggle_update_button.setText("Activate")

    def toggleActivateButtonText(self) -> None:
        """Toggle the text of update button."""
        if self.gui.toggle_update_button.text() == "Activate":
            self.gui.toggle_update_button.setText("Deactivate")
        else:
            self.gui.toggle_update_button.setText("Activate")

    def changeWindowsUpdate(self) -> None:
        """Change the state and status of windows update."""
        if self.gui.toggle_update_button.text() == "Activate":
            self.runActions([Action.ENABLE])
        else:
            self.runActions([Action.DISABLE, Action.STOP])

    def changeServiceStatus(self, service: Service) -> None:
        """Change the status (start/stop) of a service."""
        status_button, _ = self.gui.ins_dict[service.service_name]
        if status_button.text() == "Start":
            self.runServices(Action.START, [service])
        else:
            self.runServices(Action.STOP, [service])

    def changeServiceState(self, service: Service) -> None:
        """Change the state (enable/disable) of a service."""
        _, state_button = self.gui.ins_dict[service.service_name]
        if state_button.text() == "Enable":
            self.runServices(Action.ENABLE, [service])
        else:
            self.runServices(Action.DISABLE, [service])

    def setAutomaticUpdates(self, checked: bool) -> None:
        """Set automatic windows updates.

        Args:
            checked: True to enable, False to disable.
        """
        try:
            set_automatic_updates(checked)
        except OSError as e:
            if checked:
                msg = f"Failed to enable automatic windows update\n\n{e}"
            else:
                msg = f"Failed to disable automatic windows update\n\n{e}"
            self.message_bar.displayMessage(msg, True)
        else:
            if checked:
                msg = "Enabled automatic windows update"
            else:
                msg = "Disabled automatic windows update"
            self.promptRestart(msg + ", restart to confirm changes?")

    def setAutomaticDriversUpdates(self, checked: bool) -> None:
        """Set automatic drivers updates on windows update.

        Args:
            checked: True to enable, False to disable.
        """
        try:
            set_automatic_drivers_updates(checked)
        except OSError as e:
            if checked:
                msg = f"Failed to enable automatic drivers update\n\n{e}"
            else:
                msg = f"Failed to disable automatic drivers update\n\n{e}"
            self.message_bar.displayMessage(msg, True)
        else:
            if checked:
                msg = "Enabled automatic drivers update"
            else:
                msg = "Disabled automatic drivers update"
            self.promptRestart(msg + ", restart to apply changes?")

    def runServices(self, action: Action, services: ServicesType | None = None) -> None:
        """Run the specified action on the services in a new thread."""
        if self._thread.isRunning():
            return self.message_bar.displayMessage(
                "Thread Busy, Please wait for the current operation to finish.", True
            )
        if services is None:
            services = self.services

        match action:
            case Action.START:
                msg = "Starting"
            case Action.STOP:
                msg = "Stopping"
            case Action.ENABLE:
                msg = "Enabling"
            case Action.DISABLE:
                msg = "Disabling"
                self._thread.connectPreDisable(
                    config.backup, (svc.service_name for svc in services),
                    self.backup_dir, self.filename
                )  # backup services before disabling.

        if len(services) != 1:
            msg += " services..."
        else:
            msg += " service: %s" % services[0].display_name

        self.message_bar.displayMessage(msg)
        self._current_services = services
        self._thread.start(action, services)

    def runActions(self, actions: list[Action]) -> None:
        """Run actions concurrently using action callbacks queue."""
        if self._thread.isRunning():
            return self.message_bar.displayMessage(
                "Thread Busy, Please wait for the current operation to finish.", True
            )

        for action in actions:
            self._action_callbacks.append(partial(self.runServices, action))

        self._processActions()

    def _processActions(self) -> None:
        if not self._action_callbacks:
            return
        self._action_callbacks.popleft()()
        # if it was last action callback.
        if not self._action_callbacks:
            self.toggleActivateButtonText()

    def promptRestart(self, message: str) -> None:
        """Prompt the user to restart the system."""
        self.message_bar.setConfirmText("Restart")
        self.message_bar.displayPrompt(message)
        self.message_bar.connect(power.restart)

    def handleFinishedServices(self, action: Action, failed_services: FailedServicesType, restart_required: bool) -> None:
        """Handle finished services and show success/error message and update states/statuses."""
        services = self._current_services
        failed_service_names = {svc.service_name for svc, _ in failed_services}

        match action:
            case Action.START:
                phrase = "started"
                for svc in services:
                    if svc.service_name in failed_service_names:
                        continue
                    status_button, _ = self.gui.ins_dict[svc.service_name]
                    status_button.setText("Stop")

                self.updateWindowsUpdateStatus()

            case Action.STOP:
                phrase = "stopped"
                for svc in services:
                    if svc.service_name in failed_service_names:
                        continue
                    status_button, _ = self.gui.ins_dict[svc.service_name]
                    status_button.setText("Start")

                    status_result = service.status(svc.service_name)
                    info_result = service.info(svc.service_name)
                    if status_result.value is None or info_result.value is None:
                        status_button.setEnabled(True)
                    elif status_result.value[1] in (1, 3) and info_result.value[
                            'start_type'] == 'disabled':  # stopped/stopping and disabled
                        status_button.setDisabled(True)

                self.updateWindowsUpdateStatus()

            case Action.ENABLE:
                phrase = "enabled"
                for svc in services:
                    if svc.service_name in failed_service_names:
                        continue
                    status_button, state_button = self.gui.ins_dict[svc.service_name]
                    status_button.setEnabled(True)
                    state_button.setText("Disable")

            case Action.DISABLE:
                phrase = "disabled"
                for svc in services:
                    if svc.service_name in failed_service_names:
                        continue
                    status_button, state_button = self.gui.ins_dict[svc.service_name]
                    status_result = service.status(svc.service_name)
                    if status_result.value is None:
                        status_button.setEnabled(True)
                    elif status_result.value[1] in (1, 3):  # stopped/stopping
                        status_button.setDisabled(True)
                    state_button.setText("Enable")

        if not failed_services and restart_required:  # prompt restart.
            if len(services) == 1:
                prompt_msg = f"Service: {services[0].display_name!r} " + \
                    "start_type change requires restart. Restart Now?"
            else:
                prompt_msg = "These services start_type changes requires restart. Restart Now?"

            self.promptRestart(prompt_msg)

        elif not failed_services:
            if len(services) == 1:
                message = f"Successfully {phrase} service: " + \
                    services[0].display_name
            else:
                message = f"Successfully {phrase} services."

            self.message_bar.displayMessage(message)
        else:
            if len(failed_services) == 1:
                _service, error = failed_services[0]
                message = error
            else:
                message = f"Failed to {action.value} services:\n"
                for _service, error in failed_services:
                    message += f"\n{error}\n"
                message = message[:-1]

            self.message_bar.displayMessage(message, True)
