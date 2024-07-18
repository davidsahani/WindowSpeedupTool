import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QWidget,
)

from utils import config, power, styles
from utils.config_parser import (
    Error,
    Service,
    ServiceConfig,
    ServicesConfig,
    ServicesConfigType,
)
from widgets.message_bar import MessageBar
from widgets.stacked_widget import StackedWidget

from .confirm_widget import ConfirmActionWidget
from .error_window import ErrorWindow
from .services_thread import (  # noqa
    Action,
    FailedServicesType,
    ServicesThread,
    ServicesType,
)
from .services_widget import ServicesWidget, ServiceWidget


class WindowServices(QFrame):
    def __init__(self, parent: StackedWidget) -> None:
        super().__init__(parent)
        self._parent = parent
        self.setupWidgets()
        self.setMainWidget()
        self.setStyleSheet(styles.get("services"))
        self.progressbar_widget.hide()  # hide initially.

    def setupWidgets(self) -> None:
        """Setup the widgets in layout."""
        self.scroll_widget = QScrollArea()
        self.scroll_widget.setWidgetResizable(True)
        self.scroll_widget.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_widget.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_widget.setContentsMargins(0, 0, 0, 0)

        self.message_bar = MessageBar()
        self.progressbar = QProgressBar()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("ProgressCancelButton")

        self.progressbar_widget = QWidget()
        progress_bar_layout = QGridLayout()
        progress_bar_layout.addWidget(self.progressbar, 0, 0)
        progress_bar_layout.addWidget(self.cancel_button, 0, 1)
        progress_bar_layout.setContentsMargins(0, 0, 0, 0)
        self.progressbar_widget.setLayout(progress_bar_layout)

        self.recover_widget = self.createRecoverWidget()
        margins = self.recover_widget.contentsMargins()
        margins.setTop(0)  # set top margin to zero.
        self.recover_widget.setContentsMargins(margins)

        layout = QGridLayout()
        layout.addWidget(self.scroll_widget, 0, 0)
        layout.addWidget(self.recover_widget, 1, 0)
        layout.addWidget(self.message_bar, 2, 0)
        layout.addWidget(self.progressbar_widget, 3, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setAlignment(self.message_bar, Qt.AlignmentFlag.AlignBottom)
        layout.setAlignment(self.progressbar_widget,
                            Qt.AlignmentFlag.AlignBottom)
        layout.setAlignment(self.recover_widget, Qt.AlignmentFlag.AlignBottom |
                            Qt.AlignmentFlag.AlignRight)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self._layout = layout

    def setMainWidget(self) -> None:
        """Set the main widget of the scroll area."""
        try:
            main_widget = self.createMainWidget()
            self.scroll_widget.setWidget(main_widget)
            self.connectSlots()  # setup thread and its callbacks.
            # resize main window to properly show services.
            main_parent_widget = self._getMainParentWidget()
            if not main_parent_widget.isMaximized() and \
                    main_parent_widget.width() < 860:
                main_parent_widget.resize(860, 560)

        except (OSError, Error) as e:
            self.message_bar.message_close.enable_timer = False
            self.message_bar.displayMessage(str(e), True)
            self.message_bar.setRetryStyleForCloseButton(True)
            self.message_bar.message_close.close_button.setText("Reload")
            self.message_bar.connectClose(self.setMainWidget)
            self.recover_widget.hide()
        else:
            self.recover_widget.show()
            self.message_bar.connectClose(lambda: None)
            self.message_bar.setRetryStyleForCloseButton(False)
            self.message_bar.message_close.enable_timer = True

    def _getMainParentWidget(self) -> QWidget:
        widget = self._parent
        while True:
            w = widget.parentWidget()
            if w is None:
                break
            else:
                widget = w
        return widget

    def createMainWidget(self) -> QWidget:
        """Load configuration and create the main services widget."""
        self.config = config.load()
        return self.createServicesWidget(self.config.Services)

    def createServicesWidget(self, services_config: ServicesConfigType) -> QWidget:
        """Create and return a widget containing all services based on the configuration."""
        size_policy = QSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        layout = QGridLayout()

        for row, config_item in enumerate(services_config):
            if isinstance(config_item, ServiceConfig):
                widget = ServiceWidget(
                    config_item,
                    self.message_bar,
                )
                widget.setSizePolicy(size_policy)
                layout.addWidget(widget, row, 0)
                widget.connect(self.promptRestart)

            elif isinstance(config_item, ServicesConfig):
                widget = ServicesWidget(
                    config_item,
                    self.config.config_dir,
                    self.config.backup_dir,
                    self.message_bar,
                )
                widget.setSizePolicy(size_policy)
                layout.addWidget(widget, row, 0)
                widget.connect(self.fireAction)

            if not isinstance(config_item, list):
                continue

            for col, inner_config_item in enumerate(config_item):
                if isinstance(inner_config_item, ServiceConfig):
                    widget = ServiceWidget(
                        inner_config_item,
                        self.message_bar,
                    )
                    widget.setSizePolicy(size_policy)
                    layout.addWidget(widget, row, col)
                    widget.connect(self.promptRestart)

                else:
                    widget = ServicesWidget(
                        inner_config_item,
                        self.config.config_dir,
                        self.config.backup_dir,
                        self.message_bar,
                    )
                    widget.setSizePolicy(size_policy)
                    layout.addWidget(widget, row, col)
                    widget.connect(self.fireAction)

        widget = QWidget()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)
        return widget

    def createRecoverWidget(self) -> QGroupBox:
        """Create a widget for recovering services."""
        revert_button = QPushButton("Revert")
        restore_button = QPushButton("Restore")

        revert_button.setObjectName("RecoverButton")
        restore_button.setObjectName("RecoverButton")

        revert_button.setToolTip("Disable backed-up services.")
        restore_button.setToolTip("Enable backed-up services.")

        revert_button.clicked.connect(self.revert)
        restore_button.clicked.connect(self.restore)

        size_policy = QSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        revert_button.setSizePolicy(size_policy)
        restore_button.setSizePolicy(size_policy)

        widget = QGroupBox()
        layout = QGridLayout()
        layout.addWidget(revert_button, 0, 0)
        layout.addWidget(restore_button, 0, 1)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        widget.setLayout(layout)
        return widget

    def connectSlots(self) -> None:
        """Connect the callbacks to their corresponding events."""
        self._thread = ServicesThread()
        self._thread.started.connect(self.progressbar_widget.show)
        self._thread.finished.connect(self.progressbar_widget.hide)
        self._thread.progress.connect(self.updateProgressbar)
        self._thread.connectFinished(self.handleFailedServices)
        self.cancel_button.clicked.connect(self._thread.cancel)

    def fireAction(self, action: Action, services: ServicesType, filename: str | None = None) -> None:
        """Open confirmation widget and start the corresponding action on confirmation."""
        widget = ConfirmActionWidget(
            self._parent, services, action != Action.ENABLE
        )
        self._parent.addWidget(widget, dispose=True)
        self._parent.setCurrentWidget(widget)

        widget.setConfirmText(action.value.capitalize())
        widget.displayPrompt(f"Do you want to {action.value} these services?")
        widget.connect(lambda svcs: self.runServices(action, svcs, filename))

    def runServices(self, action: Action, services: ServicesType, filename: str | None) -> None:
        """Run the specified action on the provided services in a new thread."""
        if self._thread.isRunning():
            return self.message_bar.displayMessage(
                "Thread Busy, Please wait for the current operation to finish.", True
            )

        match action:
            case Action.START:
                self.progressbar.setFormat("Starting services: %v/%m (%p%)")
            case Action.STOP:
                self.progressbar.setFormat("Stopping services: %v/%m (%p%)")
            case Action.ENABLE:
                self.progressbar.setFormat("Enabling services: %v/%m (%p%)")
            case Action.DISABLE:
                self.progressbar.setFormat("Disabling services: %v/%m (%p%)")
                if filename is None:
                    self._thread.connectPreDisable(lambda: None)
                else:  # backup services before disabling.
                    self._thread.connectPreDisable(
                        config.backup, (svc.service_name for svc in services),
                        self.config.backup_dir, filename
                    )

        self.progressbar.setRange(0, len(services))
        self._thread.start(action, services)

    def updateProgressbar(self, value: int) -> None:
        """Update the progressbar"""
        self.progressbar.setValue(value)
        if value < self.progressbar.maximum():
            return
        # hide progressbar widget on complete.
        self.progressbar_widget.hide()

    def promptRestart(self, message: str | None = None) -> None:
        """Prompt the user to restart the system."""
        self.message_bar.setConfirmText("Restart")
        self.message_bar.displayPrompt(
            message or "These services start_type changes requires restart. Restart Now?"
        )
        self.message_bar.connect(power.restart)

    def revert(self) -> None:
        """Disable backed-up services."""
        services = self.getBackedUpServices(self.config.Services)
        if services is None:
            return
        if services:
            self.fireAction(Action.DISABLE, services)
        else:
            self.message_bar.displayMessage(
                "No backed-up services found to disable."
            )

    def restore(self) -> None:
        """Enable backed-up services."""
        services = self.getBackedUpServices(self.config.Services)
        if services is None:
            return
        if services:
            self.fireAction(Action.ENABLE, services)
        else:
            self.message_bar.displayMessage(
                "No backed-up services found to enable."
            )

    def getBackedUpServices(self, services_config: ServicesConfigType) -> ServicesType | None:
        """Return services from the backup directory based on the given configuration."""
        backup_dir = config.abs_path(self.config.backup_dir)

        if not os.path.exists(backup_dir):
            return self.message_bar.displayMessage(
                "No services have been backed up. " +
                f"Backup directory not found: '{self.config.backup_dir}'"
            )

        filenames: list[str] = []

        for config_item in services_config:
            if isinstance(config_item, ServicesConfig):
                filenames.append(config_item.filename)

            if not isinstance(config_item, list):
                continue

            for inner_config_item in config_item:
                if isinstance(inner_config_item, ServicesConfig):
                    filenames.append(inner_config_item.filename)

        services: ServicesType = []

        for filename in filenames:
            path = os.path.join(backup_dir, filename)
            if not os.path.exists(path):
                continue

            try:
                services_dict = config.read_file(path)
            except OSError as e:
                self.message_bar.displayMessage(str(e), True)
                continue

            services.extend((
                Service(service_name=name,
                        startup_type=value[0],
                        display_name=value[1])
                for name, value in services_dict.items()
            ))

        return services

    # **************************************************************************
    #                           HANDLE ERRORS                                  *
    # **************************************************************************

    def handleFailedServices(self, action: Action, services: FailedServicesType, restart_required: bool) -> None:
        """Handle failed services and show error message if any services fail."""
        if not services:
            if restart_required:
                self.promptRestart()
            return  # on success.

        if len(services) == 1:
            _service, error = services[0]
            return self.message_bar.displayMessage(error, True)

        services_length = self.progressbar.maximum()
        ratio = f"{len(services)}/{services_length}"
        message = f"{ratio} services failed to " + \
            f"{action.value}. Would you like to see them?"

        # prompt user to show failed services.
        self.message_bar.setConfirmText("Show")
        self.message_bar.displayPrompt(message, True)
        self.message_bar.connect(self.openFailedServicesWindow, action, services)  # noqa

    def openFailedServicesWindow(self, action: Action, services: FailedServicesType) -> None:
        """Display failed services in a new error window."""
        message = f"Failed to {action.value} these services..."
        self.err_win = ErrorWindow(services)
        self.err_win.displayMessage(message, True)
