from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QCheckBox, QFileDialog, QFrame, QGridLayout,
                             QGroupBox, QPushButton, QRadioButton, QScrollArea,
                             QSizePolicy, QSpacerItem, QStackedWidget,
                             QVBoxLayout, QWidget)

import styles
from src.overlay import MessageOverlay
from utils import power

from .plan_settings import PlanSettings
from .power_throttling import PowerThrottling


class ToggleSettings(QGroupBox):
    def __init__(self, parent: QWidget, message_overlay: MessageOverlay) -> None:
        super().__init__(parent)
        self.message_overlay = message_overlay
        self.setupWidgets()
        self.setStatus()
        self.connectSlots()
        self.setTitle("Enable/Disable settings")

    def setupWidgets(self) -> None:
        """Make checkboxes and set layout"""
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

    def setStatus(self) -> None:
        """Set checkboxes checked for corresponding functions"""
        checkboxes_and_functions = [
            (self.game_mode, power.is_gamemode_enabled),
            (self.fast_startup, power.is_fast_startup_enabled),
            (self.hibernation, power.is_hibernation_enabled),
            (self.usb_power_saving, power.is_usb_power_saving_enabled),
            (self.power_throttling, power.is_powerthrottling_enabled)
        ]
        for checkbox, function in checkboxes_and_functions:
            if function():
                checkbox.setChecked(True)

    def connectSlots(self) -> None:
        """Connect checkboxes and message_overlay to their corresponding methods"""
        self.game_mode.clicked.connect(self.changeGameMode)  # type: ignore
        self.fast_startup.clicked.connect(  # type: ignore
            self.changeFastStartup)
        self.hibernation.clicked.connect(  # type: ignore
            self.changeHibernation)
        self.usb_power_saving.clicked.connect(  # type: ignore
            self.changeUsbPowerSaving)
        self.power_throttling.clicked.connect(  # type: ignore
            self.changePowerThrottling)

        self.message_overlay.connect(power.restart)

    def changeGameMode(self, checked: bool) -> None:
        """Change GameMode setting based on checkbox status"""
        status = power.set_gamemode(checked)
        self.promptRestart() if not status else \
            self.displayErrorMessage(
                f"Failed to change game mode, status code: {status}")

    def changeFastStartup(self, checked: bool) -> None:
        """Change FastStartup setting based on checkbox status"""
        status = power.set_fast_startup(checked)
        self.promptRestart() if not status else \
            self.displayErrorMessage(
                f"Failed to change fast startup, status code: {status}")

    def changeHibernation(self, checked: bool) -> None:
        """Change Hibernation setting based on checkbox status"""
        status = power.set_hibernation(checked)
        self.promptRestart() if not status else \
            self.displayErrorMessage(
            f"Failed to change hibernation, status code: {status}")

    def changePowerThrottling(self, checked: bool) -> None:
        """Change PowerThrottling setting based on checkbox status"""
        status = power.set_power_throttling(checked)
        self.promptRestart() if not status else \
            self.displayErrorMessage(
                f"Failed to change power throttling, status code: {status}")

    def changeUsbPowerSaving(self, checked: bool) -> None:
        """Change Usb power saving setting based on checkbox status"""
        status = power.set_usb_power_saving(checked)
        self.promptRestart() if not status else \
            self.displayErrorMessage(
                f"Failed to change usb power saving, status code: {status}")

    def displayErrorMessage(self, message: str) -> None:
        """"Display an error message using the message overlay"""
        self.message_overlay.displayMessage(message, True)

    def promptRestart(self) -> None:
        """Prompt the user to restart the system"""
        self.message_overlay.setConfirmText("Restart")
        msg = "These changes require restart, Restart Now?"
        self.message_overlay.displayPrompt(msg)


# *================================================
# *              POWER OPTIONS                    *
# *================================================

class PowerOptions(QFrame):
    def __init__(self, parent: QStackedWidget) -> None:
        super().__init__(parent)
        self._parent = parent
        self.setupWidgets()
        self.set_power_scheme_updater()
        self.setStyleSheet(styles.get("power"))

    def set_power_scheme_updater(self) -> None:
        """Set update handler for PowerSchemes widget"""
        self._parent.currentChanged.connect(  # type: ignore
            self.update_power_scheme)
        self.__is_initial_run = True

    def update_power_scheme(self) -> None:
        """Update PowerSchemes widget when widget is changed"""
        if self._parent.currentWidget() is not self:
            return
        if self.__is_initial_run:
            self.__is_initial_run = False
            return
        self.grid.removeWidget(self.power_scheme_group_box)
        self.power_scheme_group_box.deleteLater()
        self.power_scheme_group_box = self.makePowerSchemeGroupBox()
        self.grid.addWidget(self.power_scheme_group_box, 0, 0)

    def setupWidgets(self) -> None:
        """Setup the widgets in scroll widget"""
        self.message_overlay = MessageOverlay(self)
        scroll_widget = QScrollArea(self)
        scroll_widget.setWidgetResizable(True)
        scroll_widget.setFrameShape(QFrame.Shape.NoFrame)
        scroll_widget.setWidget(self.makeMainWidget())

        layout = QVBoxLayout()
        layout.addWidget(scroll_widget)
        layout.addWidget(self.message_overlay)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setAlignment(self.message_overlay, Qt.AlignmentFlag.AlignBottom)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def makeMainWidget(self) -> QWidget:
        """Make the main widget for power options"""
        self.power_scheme_group_box = self.makePowerSchemeGroupBox()
        add_ultra_scheme_button = QPushButton("✽ Add ultra scheme")
        add_ultra_scheme_button.clicked.connect(  # type: ignore
            self.addUltraScheme)
        import_button = QPushButton("✽ Import power scheme")
        import_button.clicked.connect(self.importScheme)  # type: ignore
        import_button.setObjectName("ImportButton")
        add_ultra_scheme_button.setObjectName("UltraSchemeButton")

        spacer = QSpacerItem(  # spacer item for extra spacing
            20, 10, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        widget = QWidget()
        layout = QGridLayout(widget)
        layout.addWidget(self.power_scheme_group_box, 0, 0)
        layout.addWidget(add_ultra_scheme_button, 1, 0)
        layout.addWidget(import_button, 2, 0)
        layout.addItem(spacer, 3, 0)  # extra spacing
        layout.addWidget(PowerThrottling(widget), 4, 0)
        layout.addItem(spacer, 5, 0)   # extra spacing
        layout.addWidget(ToggleSettings(widget, self.message_overlay), 6, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setAlignment(import_button, Qt.AlignmentFlag.AlignLeading)
        layout.setAlignment(add_ultra_scheme_button,
                            Qt.AlignmentFlag.AlignLeading)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)
        self.grid = layout
        return widget

    def makePowerSchemeGroupBox(self) -> QGroupBox:
        """Make a group box for power scheme buttons"""
        self.schemes_widgets: dict[str, tuple[QRadioButton, QPushButton]] = {}
        layout = QGridLayout()

        _, active_guid = power.active()
        for row, (name, guid) in enumerate(power.schemes()):
            radio_button = self.makePowerSchemeButtons(
                row, layout, name, guid)
            if guid == active_guid:
                radio_button.setChecked(True)

        power_scheme_group_box = QGroupBox()
        power_scheme_group_box.setTitle("Power Schemes")
        power_scheme_group_box.setLayout(layout)
        self.schemes_layout = layout
        return power_scheme_group_box

    def makePowerSchemeButtons(self, row: int, grid: QGridLayout, name: str, guid: str) -> QRadioButton:
        """Make power scheme QRadioButton and QPushButton"""
        scheme_button = QRadioButton(name)
        arrow_button = QPushButton("➣")
        scheme_button.setObjectName("SchemeButton")
        arrow_button.setObjectName("ArrowButton")
        grid.addWidget(scheme_button, row, 0)
        grid.addWidget(arrow_button, row, 1, Qt.AlignmentFlag.AlignRight)
        scheme_button.clicked.connect(  # type: ignore
            lambda: self.changePowerScheme(guid))
        arrow_button.clicked.connect(  # type: ignore
            lambda: self.openPlanSettings(name, guid))
        self.schemes_widgets[guid] = scheme_button, arrow_button
        return scheme_button

    def addUltraScheme(self) -> None:
        """Create Ultra Performance scheme"""
        layout = self.schemes_layout
        duplication_guid = "e9a42b02-d5df-448d-aa00-03f14749eb61"
        name, guid = power.duplicate_scheme(duplication_guid)
        self.makePowerSchemeButtons(layout.rowCount(), layout, name, guid)

    def importScheme(self) -> None:
        """Import a power scheme from file"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select power scheme", "", "pow (*.pow)")

        if not filepath:
            return  # if no path selected
        status = power.import_scheme(filepath)
        self.update_power_scheme()
        if not status:
            return  # on success
        msg = f"Failed to import scheme, status code: {status}"
        self.message_overlay.displayMessage(msg, True)

    def openPlanSettings(self, scheme_name: str, scheme_guid: str) -> None:
        """Open and switch to PlanSettings widget"""
        PlanSettings(self, self._parent, scheme_name, scheme_guid)

    def changePowerScheme(self, guid: str) -> None:
        """Change current active power scheme"""
        status = power.set_active(guid)
        if not status:
            return  # on success
        msg = f"Couldn't set this guid: {guid} as active"
        self.message_overlay.displayMessage(msg, True)
