from typing import Any, Callable, override

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QGridLayout, QGroupBox, QPushButton, QWidget

from utils import config, service
from utils.config_parser import (
    Button,
    ExtraButton,
    Service,
    ServiceConfig,
    ServicesConfig,
)
from widgets.message_bar import MessageBar

from .services_thread import Action, FailedServicesType, ServicesThread, ServicesType


class CheckableButton(QPushButton):
    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setCheckable(True)

    @override
    def mousePressEvent(self, e: QMouseEvent | None) -> None:
        was_checked = self.isChecked()
        super().mouseReleaseEvent(e)
        self.setChecked(was_checked)
        self.clicked.emit(was_checked)


class ServiceWidget(QGroupBox):
    _restart_required = pyqtSignal(str)

    def __init__(
        self,
        config: ServiceConfig,
        message_bar: MessageBar,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.config = config
        self.message_bar = message_bar
        self._buttons: list[tuple[Button, QPushButton]] = []
        self.setupWidgets()
        self.connectSlots()
        self.setStateAndStatus()

        self.setTitle(config.display_name)
        info = service.info(self.config.service_name).value or {}
        description = info.get("description", "Could not get description.")
        self.setToolTip(f"<div <b>Description:</b> <p>{description}</p></div>")

    def setupWidgets(self) -> None:
        """Setup the widgets in layout."""
        layout = QGridLayout()

        if not self.config.buttons:
            enable_button = CheckableButton("Enable Service")
            disable_button = CheckableButton("Disable Service")

            enable_button.clicked.connect(
                lambda: self.executeAction(Action.ENABLE))
            disable_button.clicked.connect(
                lambda: self.executeAction(Action.DISABLE))

            self._buttons.append((Button.ENABLE, enable_button))
            self._buttons.append((Button.DISABLE, disable_button))

            layout.addWidget(enable_button, 0, 0)
            layout.addWidget(disable_button, 0, 1)
        else:
            row, col = 0, 0
            length = len(self.config.buttons)
            last_row = row + (length // 2)
            are_buttons_odd = length % 2 != 0

            for button_enum in self.config.buttons:
                match button_enum:
                    case Button.START:
                        button = CheckableButton("Start Service")
                        button.clicked.connect(
                            lambda: self.executeAction(Action.START)
                        )
                    case Button.STOP:
                        button = CheckableButton("Stop Service")
                        button.clicked.connect(
                            lambda: self.executeAction(Action.STOP)
                        )
                    case Button.ENABLE:
                        button = CheckableButton("Enable Service")
                        button.clicked.connect(
                            lambda: self.executeAction(Action.ENABLE)
                        )
                    case Button.DISABLE:
                        button = CheckableButton("Disable Service")
                        button.clicked.connect(
                            lambda: self.executeAction(Action.DISABLE)
                        )

                if row == last_row and are_buttons_odd:
                    layout.addWidget(button, row, col, 1, 2)
                else:
                    layout.addWidget(button, row, col)

                row += col
                col = 0 if col else 1  # flip-flop
                self._buttons.append((button_enum, button))

        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)

    def connectSlots(self) -> None:
        """Connect the callbacks to their corresponding events."""
        self._thread = ServicesThread()
        self._thread.finished.connect(self.setStateAndStatus)
        self._thread.connectFinished(self.handleFinishedService)

    def setStateAndStatus(self) -> None:
        """Set buttons current states and statues."""
        status = service.status(self.config.service_name).value
        info = service.info(self.config.service_name).value
        is_running = status is not None and status[1] in (2, 4)
        is_disabled = (info or {}).get("start_type") == "disabled"

        for button_enum, button in self._buttons:
            match button_enum:
                case Button.START:
                    button.setChecked(is_running)
                case Button.STOP:
                    button.setChecked(not is_running)
                case Button.ENABLE:
                    button.setChecked(not is_disabled)
                case Button.DISABLE:
                    button.setChecked(is_disabled)

    def connect(self, func: Callable[[str], Any]) -> None:
        """Connect the function to restart required event.

        Receive:
            Restart message
        """
        self._restart_required.connect(func)

    def executeAction(self, action: Action) -> None:
        """Run the specified action for service in new thread."""
        phrase: str | None = None

        match action:
            case Action.START | Action.STOP:
                status = service.status(self.config.service_name).value
                is_running = status is not None and status[1] in (2, 4)
                if action == Action.START and is_running:
                    phrase = "already running"
                elif action == Action.STOP and not is_running:
                    phrase = "already stopped"

            case Action.ENABLE | Action.DISABLE:
                info = service.info(self.config.service_name).value
                is_disabled = (info or {}).get("start_type") == "disabled"
                if action == Action.ENABLE and not is_disabled:
                    phrase = "already enabled"
                elif action == Action.DISABLE and is_disabled:
                    phrase = "already disabled"

        if phrase is not None:
            return self.message_bar.displayMessage(
                f"Service: {self.config.display_name!r} is {phrase}."
            )

        if self._thread.isRunning():
            return self.message_bar.displayMessage(
                "Thread Busy, Please wait for the current operation to finish.", True
            )

        self._thread.start(action, [Service(
            service_name=self.config.service_name,
            display_name=self.config.display_name,
            startup_type=self.config.startup_type)
        ])

    def handleFinishedService(self, action: Action, services: FailedServicesType, restart_required: bool) -> None:
        """Handle finished service and show success/error message accordingly."""
        if services:
            _service, error = services[0]
            return self.message_bar.displayMessage(error, True)

        if restart_required:
            return self._restart_required.emit(
                f"Service: {self.config.display_name!r} " +
                "start_type change requires restart. Restart Now?"
            )

        match action:
            case Action.START:
                phrase = "started"
            case Action.STOP:
                phrase = "stopped"
            case Action.ENABLE:
                phrase = "enabled"
            case Action.DISABLE:
                phrase = "disabled"

        self.message_bar.displayMessage(
            f"Successfully {phrase} service: {self.config.display_name}"
        )


class ServicesWidget(QGroupBox):
    _action_dispatched = pyqtSignal(Action, list, str)

    def __init__(
        self,
        config: ServicesConfig,
        config_dir: str,
        backup_dir: str,
        message_bar: MessageBar,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.config = config
        self.config_dir = config_dir
        self.backup_dir = backup_dir
        self.message_bar = message_bar
        self.setupWidgets()
        self.connectSlots()
        self.setTitle(config.title)

    def setupWidgets(self) -> None:
        """Setup the widgets in layout."""
        self.start_button = QPushButton("Start Services")
        self.stop_button = QPushButton("Stop Services")
        self.enable_button = QPushButton("Enable Services")
        self.disable_button = QPushButton("Disable Services")

        row, col = 2, 0
        length = len(self.config.extra_buttons)
        last_row = row + (length // 2)
        are_buttons_odd = length % 2 != 0

        layout = QGridLayout()

        for extra_button in self.config.extra_buttons:
            match extra_button:
                case ExtraButton.STOP_RUNNING:
                    button = QPushButton("Stop Running Services")
                    button.clicked.connect(
                        lambda: self.dispatchActionRunning(Action.STOP)
                    )
                case ExtraButton.DISABLE_RUNNING:
                    button = QPushButton("Disable Running Services")
                    button.clicked.connect(
                        lambda: self.dispatchActionRunning(Action.DISABLE)
                    )

            if row == last_row and are_buttons_odd:
                layout.addWidget(button, row, col, 1, 2)
            else:
                layout.addWidget(button, row, col)

            row += col
            col = 0 if col else 1  # flip-flop

        layout.addWidget(self.start_button, 0, 0)
        layout.addWidget(self.stop_button, 0, 1)
        layout.addWidget(self.enable_button, 1, 0)
        layout.addWidget(self.disable_button, 1, 1)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)

    def connectSlots(self) -> None:
        """Connect the buttons' event to their corresponding action."""
        self.start_button.clicked.connect(
            lambda: self.dispatchAction(Action.START))
        self.stop_button.clicked.connect(
            lambda: self.dispatchAction(Action.STOP))
        self.enable_button.clicked.connect(
            lambda: self.dispatchAction(Action.ENABLE))
        self.disable_button.clicked.connect(
            lambda: self.dispatchAction(Action.DISABLE))

    def dispatchAction(self, action: Action, services: ServicesType | None = None) -> None:
        """Dispatch the specified action with the provided or loaded services."""
        if services is None:
            try:
                services = config.load_file(
                    self.config.filename, self.config_dir, self.backup_dir
                )
            except OSError as e:
                return self.message_bar.displayMessage(str(e), True)

        self._action_dispatched.emit(action, services, self.config.filename)

    def dispatchActionRunning(self, action: Action) -> None:
        """Dispatch the specified action with running services."""
        try:
            services = config.load_file(
                self.config.filename, self.config_dir, self.backup_dir
            )
        except OSError as e:
            return self.message_bar.displayMessage(str(e), True)

        service_names = {svc[0] for svc in service.running()}
        running_services = [
            svc for svc in services if svc.service_name in service_names
        ]
        if running_services:
            self.dispatchAction(action, running_services)
        else:
            self.message_bar.displayMessage(
                f"No services are running to {action.name.lower()}."
            )

    def connect(self, func: Callable[[Action, ServicesType, str], Any]) -> None:
        """Connect a function to handle dispatched action.

        Receive:
            Action, services, filename.
        """
        self._action_dispatched.connect(func)
