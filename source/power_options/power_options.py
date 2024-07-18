from functools import partial
from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from utils import power, styles
from widgets.message_bar import MessageBar
from widgets.stacked_widget import StackedWidget

from .plan_settings import PlanSettings
from .power_throttling import PowerThrottling


class ToggleSettings(QGroupBox):
    def __init__(self, message_bar: MessageBar, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.message_bar = message_bar
        self.setupWidgets()
        self.setStatuses()
        self.connectSlots()
        self.setTitle("Enable/Disable settings")

    def setupWidgets(self) -> None:
        """Create checkboxes and add them in layout."""
        self.game_mode = QCheckBox("GameMode")
        self.fast_startup = QCheckBox("Fast Startup")
        self.hibernation = QCheckBox("Hibernation")
        self.usb_power_saving = QCheckBox("Usb Power Saving")
        self.power_throttling = QCheckBox("PowerThrottling System Wide")

        layout = QVBoxLayout(self)
        layout.addWidget(self.game_mode)
        layout.addWidget(self.fast_startup)
        layout.addWidget(self.hibernation)
        layout.addWidget(self.usb_power_saving)
        layout.addWidget(self.power_throttling)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)

    def setStatuses(self) -> None:
        """Set checkboxes status for corresponding power settings."""
        self.game_mode.setChecked(power.is_gamemode_enabled())
        self.fast_startup.setChecked(power.is_fast_startup_enabled())
        self.hibernation.setChecked(power.is_hibernation_enabled())
        self.usb_power_saving.setChecked(power.is_usb_power_saving_enabled())
        self.power_throttling.setChecked(power.is_powerthrottling_enabled())

    def connectSlots(self) -> None:
        """Connect the callbacks to their corresponding events."""
        self.game_mode.clicked.connect(
            partial(self._executeFunc, power.set_gamemode)
        )
        self.fast_startup.clicked.connect(
            partial(self._executeFunc, power.set_fast_startup)
        )
        self.hibernation.clicked.connect(
            partial(self._executeFunc, power.set_hibernation)
        )
        self.usb_power_saving.clicked.connect(
            partial(self._executeFunc, power.set_usb_power_saving)
        )
        self.power_throttling.clicked.connect(
            partial(self._executeFunc, power.set_power_throttling)
        )
        self.message_bar.connect(power.restart)  # restart on confirm.

    def _executeFunc(self, func: Callable[[bool], None], value: bool) -> None:
        try:
            func(value)
        except Exception as error:
            notes = error.__notes__ if hasattr(error, '__notes__') else []
            msg = f"{error.__class__.__name__}: {error}\n{'\n'.join(notes)}"
            self.message_bar.displayMessage(msg, True)
        else:
            self.message_bar.setConfirmText("Restart")
            msg = "These changes require restart, Restart Now?"
            self.message_bar.displayPrompt(msg)


# *================================================*
# *               POWER OPTIONS                    *
# *================================================*


class PowerOptions(QFrame):
    def __init__(self, parent: StackedWidget) -> None:
        super().__init__(parent)
        self._parent = parent
        self._post_init()
        self.setupWidgets()
        self.setStyleSheet(styles.get("power"))

    def _post_init(self) -> None:
        self._scheme_buttons: dict[str, tuple[QRadioButton, QPushButton]] = {}
        self.__is_initial_run = True
        self._parent.currentChanged.connect(self.refresh_power_schemes)

    def refresh_power_schemes(self) -> None:
        if self._parent.currentWidget() is not self:
            return
        if self.__is_initial_run:
            self.__is_initial_run = False
            return
        self.updatePowerSchemesGroupBox()

    def setupWidgets(self) -> None:
        """Setup the widgets in layout."""
        self.message_bar = MessageBar()

        scroll_widget = QScrollArea(self)
        scroll_widget.setWidgetResizable(True)
        scroll_widget.setFrameShape(QFrame.Shape.NoFrame)
        scroll_widget.setWidget(self.createMainWidget())

        layout = QVBoxLayout()
        layout.addWidget(scroll_widget)
        layout.addWidget(self.message_bar)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setAlignment(self.message_bar, Qt.AlignmentFlag.AlignBottom)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def createMainWidget(self) -> QWidget:
        """Create the main widget for power options."""
        self.power_schemes_group_box = self.createPowerSchemesGroupBox()

        add_ultra_scheme_button = QPushButton("✽ Add ultra scheme")
        add_ultra_scheme_button.setObjectName("UltraSchemeButton")

        import_button = QPushButton("✽ Import power scheme")
        import_button.setObjectName("ImportButton")

        add_ultra_scheme_button.clicked.connect(self.addUltraScheme)
        import_button.clicked.connect(self.importScheme)

        spacer = QSpacerItem(  # spacer item for extra spacing
            20, 10, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed
        )

        widget = QWidget()
        layout = QGridLayout()
        layout.addWidget(self.power_schemes_group_box, 0, 0)
        layout.addWidget(add_ultra_scheme_button, 1, 0)
        layout.addWidget(import_button, 2, 0)
        layout.addItem(spacer, 3, 0)  # extra spacing
        layout.addWidget(PowerThrottling(self.message_bar), 4, 0)
        layout.addItem(spacer, 5, 0)   # extra spacing
        layout.addWidget(ToggleSettings(self.message_bar), 6, 0)

        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setAlignment(import_button, Qt.AlignmentFlag.AlignLeading)
        layout.setAlignment(add_ultra_scheme_button, Qt.AlignmentFlag.AlignLeading)  # noqa

        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)
        return widget  # main widget.

    def createPowerSchemesGroupBox(self) -> QGroupBox:
        """Create the group box for power schemes."""
        self.schemes_layout = QGridLayout()
        self.updatePowerSchemesGroupBox()
        power_scheme_group_box = QGroupBox()
        power_scheme_group_box.setTitle("Power Schemes")
        power_scheme_group_box.setLayout(self.schemes_layout)
        return power_scheme_group_box

    def updatePowerSchemesGroupBox(self) -> None:
        """Update the power schemes group box."""
        for guid in self._scheme_buttons.copy():
            self.removePowerSchemeButtons(guid)

        active_result = power.active()
        if active_result.value is None:
            return self.showErrorMessage(active_result.error.stderr)

        power_schemes_result = power.schemes()
        if power_schemes_result.value is None:
            return self.showErrorMessage(power_schemes_result.error.stderr)

        active_guid = active_result.value[1]

        for row, (name, guid) in enumerate(power_schemes_result.value):
            scheme_button = self.insertPowerSchemeButtons(name, guid, row)
            if guid == active_guid:
                scheme_button.setChecked(True)

    def insertPowerSchemeButtons(self, name: str, guid: str, row: int) -> QRadioButton:
        """Insert power scheme SchemeButton and ArrowButton to layout."""
        scheme_button = QRadioButton(name)
        scheme_button.setObjectName("SchemeButton")

        arrow_button = QPushButton("➣")
        arrow_button.setObjectName("ArrowButton")

        scheme_button.clicked.connect(lambda: self.changePowerScheme(guid))
        arrow_button.clicked.connect(lambda: self.openPlanSettings(name, guid))

        self.schemes_layout.addWidget(scheme_button, row, 0)
        self.schemes_layout.addWidget(
            arrow_button, row, 1, Qt.AlignmentFlag.AlignRight
        )

        self._scheme_buttons[guid] = scheme_button, arrow_button
        return scheme_button

    def removePowerSchemeButtons(self, guid: str) -> None:
        """Remove power scheme SchemeButton and ArrowButton from layout."""
        buttons = self._scheme_buttons.pop(guid, None)
        if buttons is None:
            return self.message_bar.displayMessage(
                "Failed to remove power scheme, with " +
                f"guild: {guid}, Entry doesn't exist.", True
            )
        scheme_button, arrow_button = buttons
        self.schemes_layout.removeWidget(scheme_button)
        self.schemes_layout.removeWidget(arrow_button)
        self.update()  # update the window

    def addUltraScheme(self) -> None:
        """Create Ultra Performance scheme and insert it to layout."""
        duplication_guid = "e9a42b02-d5df-448d-aa00-03f14749eb61"
        result = power.duplicate_scheme(duplication_guid)
        if result.value is None:
            return self.showErrorMessage(result.error.stderr)

        name, guid = result.value
        last_row = self.schemes_layout.rowCount()
        self.insertPowerSchemeButtons(name, guid, last_row)

    def importScheme(self) -> None:
        """Import a power scheme from file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select power scheme", "", "pow (*.pow)")

        if not filepath:
            return  # no path selected

        result = power.import_scheme(filepath)
        if result.status == 0:
            self.updatePowerSchemesGroupBox()
        else:
            self.showErrorMessage(result.error)

    def changePowerScheme(self, guid: str) -> None:
        """Change current active power scheme."""
        result = power.set_active(guid)
        if result.status != 0:
            self.showErrorMessage(result.error)

    def showErrorMessage(self, error: str) -> None:
        self.message_bar.displayMessage(error, True)

    def openPlanSettings(self, scheme_name: str, scheme_guid: str) -> None:
        """Open plan settings for selected power scheme."""
        widget = PlanSettings(self._parent, scheme_name, scheme_guid)
        self._parent.addWidget(widget, dispose=True)
        self._parent.setCurrentWidget(widget)
