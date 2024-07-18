from functools import partial
from typing import Callable, override

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from utils import power, styles
from widgets.message_bar import MessageBar
from widgets.stacked_widget import StackedWidget


class ExpandableInputButton(QWidget):
    """A Button that expands to reveal an input field and action buttons."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.text = text
        self.setupWidgets()
        self.__function = None

    def setupWidgets(self) -> None:
        """Setup the widgets in layout."""
        self.expand_button = QPushButton(self.text)
        self.expand_button.clicked.connect(self.onPress)

        self.input_action_panel = self.createInputActionPanel()
        self.input_action_panel.hide()  # hide initially.

        layout = QGridLayout()
        layout.addWidget(self.expand_button, 0, 0)
        layout.addWidget(self.input_action_panel, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(400)
        self.setLayout(layout)

    def createInputActionPanel(self) -> QWidget:
        """Create the input field, confirm and cancel buttons."""
        self.line_edit = QLineEdit()
        self.line_edit.setMinimumWidth(210)

        self.confirm_button = QPushButton("Confirm")
        self.cancel_button = QPushButton("Cancel")

        self.confirm_button.clicked.connect(self.onConfirm)
        self.cancel_button.clicked.connect(self.onCancel)

        widget = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(self.line_edit)
        layout.addWidget(self.cancel_button)
        layout.addWidget(self.confirm_button)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeading)
        layout.setAlignment(self.line_edit, Qt.AlignmentFlag.AlignLeading)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)
        return widget

    @override
    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        """Handle key presses for the input field."""
        if not self.line_edit.hasFocus() or a0 is None:
            return
        key = a0.key()
        if key == Qt.Key.Key_Escape:
            self.onCancel()
            return
        if key in (Qt.Key.Key_Return,
                   Qt.Key.Key_Enter):
            self.onConfirm()

    def setPlaceholderText(self, text: str) -> None:
        """Set the placeholder text for input field."""
        self.line_edit.setPlaceholderText(text)

    def setConfirmText(self, text: str) -> None:
        """Set the text of confirm button."""
        self.confirm_button.setText(text)

    def setCancelText(self, text: str) -> None:
        """Set the text of cancel button."""
        self.cancel_button.setText(text)

    def connect(self, function: Callable[[str], bool]) -> None:
        """Connect a callback function to be called upon confirming the input.

        If function returns True, input action panel will be hidden otherwise stay visible.
        In either case input text field will be cleared.

        Args:
            function: The callback to be executed when the confirm button is clicked.

        Receive:
            input field text
        """
        self.__function = function

    def onConfirm(self) -> None:
        """Clear line-edit and call connected function."""
        function = self.__function
        if function is None:
            return self.onCancel()
        if function(self.line_edit.text()):
            self.onCancel()
        self.line_edit.clear()

    def onPress(self) -> None:
        """Hide expand button and show input action panel."""
        self.expand_button.hide()
        self.input_action_panel.show()

    def onCancel(self) -> None:
        """Hide input action panel and show expand button."""
        self.input_action_panel.hide()
        self.expand_button.show()


class DisplaySleepTimeout(QGroupBox):
    def __init__(self, scheme_guid: str, message_bar: MessageBar, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.scheme_guid = scheme_guid
        self.message_bar = message_bar
        self.setupWidgets()
        self.connectSlots()
        self.callbacks: list[tuple[Callable[[str], None], str]] = []

    def setupWidgets(self) -> None:
        """Setup the widgets in layout."""
        display_result = power.get_display_timeout(self.scheme_guid)
        if display_result.value is None:
            self.message_bar.displayMessage(display_result.error.stderr, True)

        sleep_result = power.get_sleep_timeout(self.scheme_guid)
        if sleep_result.value is None:
            self.message_bar.displayMessage(sleep_result.error.stderr, True)

        ac_display_timeout, dc_display_timeout = display_result.value or (0, 0)
        ac_sleep_timeout, dc_sleep_timeout = sleep_result.value or (0, 0)

        self.ac_display_combobox = self.createTimeoutCombobox(ac_display_timeout)  # noqa
        self.ac_sleep_combobox = self.createTimeoutCombobox(ac_sleep_timeout)

        self.dc_display_combobox = self.createTimeoutCombobox(dc_display_timeout)  # noqa
        self.dc_sleep_combobox = self.createTimeoutCombobox(dc_sleep_timeout)

        ac_widget = self.createDisplaySleepComboboxesWidget(
            self.ac_display_combobox, self.ac_sleep_combobox
        )
        dc_widget = self.createDisplaySleepComboboxesWidget(
            self.dc_display_combobox, self.dc_sleep_combobox
        )

        size_policy = QSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum
        )

        tab_widget = QTabWidget()
        tab_widget.addTab(ac_widget, "AC")
        tab_widget.addTab(dc_widget, "DC")

        self.setSizePolicy(size_policy)
        tab_widget.setSizePolicy(size_policy)

        layout = QVBoxLayout(self)
        layout.addWidget(tab_widget)
        self.setLayout(layout)

    def connectSlots(self) -> None:
        """Connect slots for the display and sleep comboboxes."""
        self.ac_display_combobox.currentTextChanged.connect(
            partial(self.saveCallback, self.changeAcDisplayTimeout)
        )
        self.ac_sleep_combobox.currentTextChanged.connect(
            partial(self.saveCallback, self.changeAcSleepTimeout)
        )
        self.dc_display_combobox.currentTextChanged.connect(
            partial(self.saveCallback, self.changeDcDisplayTimeout)
        )
        self.dc_sleep_combobox.currentTextChanged.connect(
            partial(self.saveCallback, self.changeDcSleepTimeout)
        )
        # connect message bar confirm button for save changes.
        self.message_bar.connect(self.onSaveChanges)

    def createTimeoutCombobox(self, timeout: int) -> QComboBox:
        minutes = [2, 3, 5, 10, 15, 20, 25, 30, 35, 45]  # time options.
        times = ['1 minute'] + [f'{minute} minutes' for minute in minutes] + \
            ['1 hour'] + [f'{hour} hours' for hour in range(2, 6)] + ['never']

        timeout_combobox = QComboBox()
        timeout_combobox.addItems(times)

        time = self.format_time(timeout)
        if time not in times:
            timeout_combobox.addItem(time)

        timeout_combobox.setCurrentText(time)
        return timeout_combobox

    def createDisplaySleepComboboxesWidget(self, display_combobox: QComboBox, sleep_combobox: QComboBox) -> QWidget:
        """Create a widget for display and sleep comboboxes."""
        display_icon = QPushButton()
        sleep_icon = QPushButton()

        display_icon.setObjectName("DisplayIcon")
        sleep_icon.setObjectName("SleepIcon")

        display_label = QLabel("Turn off the display after:")
        sleep_label = QLabel("Put the computer to sleep after:")

        widget = QWidget()
        layout = QGridLayout()
        layout.addWidget(display_icon, 0, 0)
        layout.addWidget(sleep_icon, 1, 0)
        layout.addWidget(display_label, 0, 1)
        layout.addWidget(sleep_label, 1, 1)
        layout.addWidget(display_combobox, 0, 2)
        layout.addWidget(sleep_combobox, 1, 2)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeading)
        # set minimum width for comboboxes.
        display_combobox.setMinimumWidth(150)
        sleep_combobox.setMinimumWidth(150)
        widget.setLayout(layout)
        return widget

    def saveCallback(self, func: Callable[[str], None], value: str) -> None:
        """Save callback to be called upon saving changes."""
        self.callbacks.append((func, value))
        self.message_bar.setConfirmText("Save changes")
        self.message_bar.displayPrompt("Do you want to save these changes?")

    def onSaveChanges(self) -> None:
        """Execute callbacks on save changes."""
        for func, value in self.callbacks:
            func(value)
        self.callbacks.clear()

    def changeAcDisplayTimeout(self, value: str) -> None:
        """Change monitor timeout to given value."""
        self.changeTimeout('monitor-timeout-ac', value)

    def changeAcSleepTimeout(self, value: str) -> None:
        """Change system sleep timeout to given value."""
        self.changeTimeout('standby-timeout-ac', value)

    def changeDcDisplayTimeout(self, value: str) -> None:
        """Change monitor timeout to given value."""
        self.changeTimeout('monitor-timeout-dc', value)

    def changeDcSleepTimeout(self, value: str) -> None:
        """Change system sleep timeout to given value."""
        self.changeTimeout('standby-timeout-dc', value)

    def changeTimeout(self, setting: str, value: str) -> None:
        """Change the specified timeout to the given value."""
        minute = self.parse_time(value)
        active_result = power.active()
        if active_result.value is None:
            return self.message_bar.displayMessage(
                active_result.error.stderr, True
            )
        active_guid = active_result.value[1]

        result = power.set_active(self.scheme_guid)
        if result.status != 0:
            return self.message_bar.displayMessage(result.error, True)

        result = power.change_setting_value(setting, minute)
        if result.status != 0:
            self.message_bar.displayMessage(result.error, True)

        result = power.set_active(active_guid)
        if result.status != 0:
            self.message_bar.displayMessage(result.error, True)

    @staticmethod
    def parse_time(value: str) -> int:
        if value == 'never':
            return 0
        minute, unit = value.split()
        minute = int(minute)
        if unit in ['hour', 'hours']:
            minute *= 60
        return minute

    @staticmethod
    def format_time(minute: int) -> str:
        if minute == 0:
            res = 'never'
        elif minute == 1:
            res = '1 minute'
        elif minute == 60:
            res = '1 hour'
        elif minute > 60 and minute in range(120, 360, 60):
            res = f'{minute // 60} hours'
        else:
            res = f'{minute} minutes'
        return res


# *================================================*
# *                PLAN SETTINGS                   *
# *================================================*


class PlanSettings(QFrame):
    def __init__(self, parent: StackedWidget, scheme_name: str, scheme_guid: str) -> None:
        super().__init__(parent)
        self._parent = parent
        self.scheme_name = scheme_name
        self.scheme_guid = scheme_guid
        self.setupWidgets()
        self.setStyleSheet(styles.get("plan_settings"))

    def setupWidgets(self) -> None:
        """Set the widgets in layout."""
        self.message_bar = MessageBar()

        self.top_label = QLabel(
            f"Change settings for the plan: {self.scheme_name}"
        )
        self.top_label.setMargin(10)
        self.top_label.setObjectName("TopLabel")

        timeout_widget = DisplaySleepTimeout(
            self.scheme_guid, self.message_bar
        )

        action_widget = self.createActionWidget()

        vertical_spacer = QSpacerItem(
            20, 20, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
        )

        layout = QVBoxLayout()
        layout.addWidget(self.top_label)
        layout.addSpacing(3)
        layout.addWidget(timeout_widget)
        layout.addSpacing(20)
        layout.addWidget(action_widget)
        layout.addSpacerItem(vertical_spacer)
        layout.addWidget(self.message_bar)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setAlignment(self.message_bar, Qt.AlignmentFlag.AlignBottom)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def createActionWidget(self) -> QWidget:
        """Create action buttons widget for managing plan settings.

        Additionally, add checkboxes to enable rename and delete buttons for default schemes.
        """
        rename_button = ExpandableInputButton("Change Scheme Name")
        rename_button.setPlaceholderText("Enter new scheme name")
        rename_button.setConfirmText("Change")

        duplicate_button = ExpandableInputButton("Duplicate Scheme")
        duplicate_button.setPlaceholderText("Enter destination guid - Optional")  # noqa
        duplicate_button.setConfirmText("Duplicate")

        export_button = QPushButton("Export this Scheme")
        delete_button = QPushButton("Delete this Scheme")
        advance_settings_button = QPushButton("Open Advanced Settings")

        rename_button.connect(self.changeSchemeName)
        duplicate_button.connect(self.duplicateScheme)
        export_button.clicked.connect(self.exportScheme)
        delete_button.clicked.connect(self.deleteScheme)
        advance_settings_button.clicked.connect(power.launch_advanced_settings)

        widget = QWidget()
        layout = QGridLayout()
        layout.addWidget(rename_button, 0, 0)
        layout.addWidget(duplicate_button, 1, 0)
        layout.addWidget(export_button, 2, 0)
        layout.addWidget(delete_button, 3, 0)
        layout.addWidget(advance_settings_button, 4, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        widget.setLayout(layout)

        if self.scheme_guid not in power.DEFAULT_SCHEME_GUIDS:
            return widget

        rename_button.setDisabled(True)  # disable rename button.
        delete_button.setDisabled(True)  # disable delete button.
        # for default schemes, add checkboxes to make enabling them harder
        # since these settings shouldn't be changed recklessly or by mistake.
        rename_checkbox = QCheckBox()
        delete_checkbox = QCheckBox()
        # enable/disable rename and delete buttons using checkboxes.
        rename_checkbox.clicked.connect(rename_button.setEnabled)
        delete_checkbox.clicked.connect(delete_button.setEnabled)
        # add rename and delete checkboxes to the layout.
        layout.addWidget(rename_checkbox, 0, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(delete_checkbox, 3, 0, Qt.AlignmentFlag.AlignLeft)
        # show/hide rename button's checkbox as per visibility.
        rename_button.expand_button.clicked.connect(rename_checkbox.hide)
        rename_button.cancel_button.clicked.connect(rename_checkbox.show)
        return widget

    def changeSchemeName(self, scheme_name: str) -> bool:
        """Change the name of the current scheme."""
        if not power.re.fullmatch(r"^(?!\s)[A-Za-z0-9\s]{3,}(?!\s)$", scheme_name):
            self.message_bar.displayMessage(
                f"Invalid scheme name: {scheme_name!r}", True)
            return False  # as failed.

        scheme_name = scheme_name.strip()  # remove whitespaces.
        result = power.change_name(self.scheme_guid, scheme_name)

        if result.status != 0:
            self.message_bar.displayMessage(result.error, True)
            return False  # as failed.

        self.top_label.setText(f"Change settings for the plan: {scheme_name}")
        self.message_bar.displayMessage(
            f"Changed scheme name {self.scheme_name!r} -> {scheme_name!r}"
        )
        self.scheme_name = scheme_name
        return True  # as success.

    def duplicateScheme(self, destination_guid: str = "") -> bool:
        """Duplicate the current scheme to destination guid."""
        if destination_guid and not power.re.match(power.GUID_PATTERN, destination_guid):
            self.message_bar.displayMessage(
                f"Invalid scheme guid: {destination_guid}", True)
            return False  # as failed.

        result = power.duplicate_scheme(self.scheme_guid, destination_guid)
        if result.value is None:
            self.message_bar.displayMessage(result.error.stderr, True)
            return False  # as failed.

        self.message_bar.displayMessage(
            f"Duplicated {self.scheme_name!r} -> guid: {result.value[1]}"
        )
        return True  # as success.

    def exportScheme(self) -> None:
        """Export the current scheme to file."""
        filepath, _ = QFileDialog.getSaveFileName(
            self, f"Save {self.scheme_name} Scheme",
            f"{self.scheme_name}.pow", "pow (*.pow)"
        )

        if not filepath:
            return  # no path selected.

        result = power.export_scheme(filepath, self.scheme_guid)

        if result.status != 0:
            self.message_bar.displayMessage(result.error, True)
        else:
            self.message_bar.displayMessage(
                f"Successively exported scheme: {self.scheme_name!r}"
            )

    def deleteScheme(self) -> None:
        """Delete the current scheme."""
        answer = QMessageBox.warning(
            self, "Are you sure you want to delete this plan?",
            "This plan can't be restored after you delete it.",
            QMessageBox.StandardButton.Ok |
            QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel
        )
        if answer == QMessageBox.StandardButton.Cancel:
            return  # on cancel.

        result = power.delete_scheme(self.scheme_guid)
        if result.status == 0:
            return self._parent.switchToPreviousWidget()
        self.message_bar.displayMessage(result.error, True)
