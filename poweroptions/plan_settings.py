from typing import Callable, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QFrame,
                             QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                             QLineEdit, QMessageBox, QPushButton, QSizePolicy,
                             QSpacerItem, QStackedWidget, QTabWidget,
                             QVBoxLayout, QWidget)

import styles
from utils import power
from widgets.overlay import MessageOverlay


class InputButton(QWidget):
    """A Button for getting user input"""

    def __init__(self, text: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.text = text            # text for front pushbutton
        self.__function = None      # function for confirm click
        self.setupWidgets()

    def setupWidgets(self) -> None:
        """setup the widgets in layout"""
        self.button = QPushButton(self.text)
        self.button.clicked.connect(self.onPress)  # type: ignore
        self.input_widget = self.makeInputWidget()
        self.input_widget.hide()  # hide initially

        layout = QGridLayout(self)
        layout.addWidget(self.button, 0, 0)
        layout.addWidget(self.input_widget, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(400)
        self.setLayout(layout)

    def makeInputWidget(self) -> QWidget:
        """Make the input field and confirm/cancel buttons"""
        self.line_edit = QLineEdit()
        self.line_edit.setMinimumWidth(210)
        self.confirm_button = QPushButton("Confirm")
        self.cancel_button = QPushButton("Cancel")
        # connect the buttons' click events to the corresponding methods
        self.confirm_button.clicked.connect(self.onConfirm)  # type: ignore
        self.cancel_button.clicked.connect(self.onCancel)  # type: ignore

        widget = QWidget(self)
        layout = QHBoxLayout(widget)
        layout.addWidget(self.line_edit)
        layout.addWidget(self.cancel_button)
        layout.addWidget(self.confirm_button)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeading)
        layout.setAlignment(self.line_edit, Qt.AlignmentFlag.AlignLeading)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)
        return widget

    def setPlaceholderText(self, text: str) -> None:
        """Set the placeholder text for the input field"""
        self.line_edit.setPlaceholderText(text)

    def setConfirmText(self, text: str) -> None:
        """Set the text of the confirm button"""
        self.confirm_button.setText(text)

    def setCancelText(self, text: str) -> None:
        """Set the text of the cancel button"""
        self.cancel_button.setText(text)

    def connect(self, function: Callable[[str], int | None]) -> None:
        """Connect the function to confirm button press event

        Receive:
            input field text
        """
        self.__function = function

    def onConfirm(self) -> None:
        """Clear line-edit and call connected function"""
        function = self.__function
        if function is None:
            return
        if not function(self.line_edit.text()):
            self.onCancel()
        self.line_edit.clear()

    def onPress(self) -> None:
        """Hide button and show input widget"""
        self.button.hide()
        self.input_widget.show()

    def onCancel(self) -> None:
        """Hide input widget and show button"""
        self.input_widget.hide()
        self.button.show()

    def keyPressEvent(self, a0: QKeyEvent) -> None:
        """Handle enter and escape key press events.

        Call onConfirm on enter key press,
        Call onCancel on escape key press
        """
        if not self.line_edit.hasFocus():
            return
        key = a0.key()
        if key == Qt.Key.Key_Escape:
            self.onCancel()
            return
        if key in (Qt.Key.Key_Return.value,
                   Qt.Key.Key_Enter.value):
            self.onConfirm()


class DisplaySleepTimeout(QGroupBox):
    def __init__(self, parent: QWidget, scheme_guid: str, message_overlay: MessageOverlay) -> None:
        super().__init__(parent)
        self.scheme_guid = scheme_guid
        self.message_overlay = message_overlay
        self.setupWidgets()
        self.selections: dict[  # to store the comboboxes selections
            QComboBox, tuple[Callable[[str], None], str]] = {}

    def setupWidgets(self) -> None:
        """Setup widgets in layout"""
        ac_display_timeout, dc_display_timeout = \
            power.get_display_timeout(self.scheme_guid)
        ac_sleep_timeout, dc_sleep_timeout = \
            power.get_sleep_timeout(self.scheme_guid)

        ac_widget, ac_display_combobox, ac_sleep_combobox = self.makeComboBoxes(
            ac_display_timeout, ac_sleep_timeout)
        dc_widget, dc_display_combobox, dc_sleep_combobox = self.makeComboBoxes(
            dc_display_timeout, dc_sleep_timeout)

        ac_display_combobox.currentTextChanged.connect(lambda text: self.mapSelection(  # type: ignore
            ac_display_combobox, self.changeAcDisplayTimeout, text))  # type: ignore
        ac_sleep_combobox.currentTextChanged.connect(lambda text: self.mapSelection(  # type: ignore
            ac_sleep_combobox, self.changeAcSleepTimeout, text))  # type: ignore
        dc_display_combobox.currentTextChanged.connect(lambda text: self.mapSelection(  # type: ignore
            dc_display_combobox, self.changeDcDisplayTimeout, text))  # type: ignore
        dc_sleep_combobox.currentTextChanged.connect(lambda text: self.mapSelection(  # type: ignore
            dc_sleep_combobox, self.changeDcSleepTimeout, text))  # type: ignore

        # connect message overlay confirm button to save changes
        self.message_overlay.connect(self.onSaveChanges)

        tab_widget = QTabWidget()
        tab_widget.addTab(ac_widget, "AC")
        tab_widget.addTab(dc_widget, "DC")
        tab_widget.setSizePolicy(  # set tab widget size policy
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        layout = QVBoxLayout(self)
        layout.addWidget(tab_widget)
        self.setSizePolicy(  # set self size policy
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.setLayout(layout)

    def makeComboBoxes(self, display_timeout: int, sleep_timeout: int)\
            -> tuple[QWidget, QComboBox, QComboBox]:
        """Make a widget with comboboxes for display and sleep timeout settings"""
        widget = QWidget()
        display_icon = QPushButton()
        sleep_icon = QPushButton()
        display_icon.setObjectName("DisplayIcon")
        sleep_icon.setObjectName("SleepIcon")
        display_label = QLabel("Turn off the display after:")
        sleep_label = QLabel("Put the computer to sleep after:")

        # Predefined time options
        minutes = [2, 3, 5, 10, 15, 20, 25, 30, 35, 45]
        times = ['1 minute'] + [f'{minute} minutes' for minute in minutes] +\
            ['1 hour'] + [f'{hour} hours' for hour in range(2, 6)] + ['never']

        display_combobox = QComboBox(widget)
        sleep_combobox = QComboBox(widget)
        display_combobox.addItems(times)
        sleep_combobox.addItems(times)

        display_time = self.format_time(display_timeout)
        sleep_time = self.format_time(sleep_timeout)
        # If current display and sleep timeouts aren't
        # in predefined options, add them to comboboxes
        if display_time not in times:
            display_combobox.addItem(display_time)
        if sleep_time not in times:
            sleep_combobox.addItem(display_time)
        # Set current display and sleep timeouts as selected in comboboxes
        display_combobox.setCurrentText(display_time)
        sleep_combobox.setCurrentText(sleep_time)

        layout = QGridLayout(widget)
        layout.addWidget(display_icon, 0, 0)
        layout.addWidget(sleep_icon, 1, 0)
        layout.addWidget(display_label, 0, 1)
        layout.addWidget(sleep_label, 1, 1)
        layout.addWidget(display_combobox, 0, 2)
        layout.addWidget(sleep_combobox, 1, 2)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeading)
        # Set minimum width for comboboxes
        display_combobox.setMinimumWidth(150)
        sleep_combobox.setMinimumWidth(150)
        widget.setLayout(layout)
        return widget, display_combobox, sleep_combobox

    def mapSelection(self, widget: QComboBox, func: Callable[[str], None], value: str) -> None:
        """Map the selected widget with its function and value, and call the connected function"""
        self.selections[widget] = (func, value)
        self.message_overlay.displayPrompt(
            "Do you want to save these changes?"
        )

    def onSaveChanges(self) -> None:
        """Execute the functions off the selections, and clear the selections"""
        for func, value in self.selections.values():
            func(value)
        self.selections.clear()

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

    @staticmethod
    def parse_time(value: str) -> int:
        if value == 'never':
            return 0
        minute, unit = value.split()
        minute = int(minute)
        if unit in ['hour', 'hours']:
            minute *= 60
        return minute

    def changeAcDisplayTimeout(self, value: str) -> None:
        """Change monitor timeout to given value"""
        minute = self.parse_time(value)
        status = power.change_setting_value('monitor-timeout-ac', minute)
        if not status:
            return  # on success
        msg = f"Failed to change ac display timeout, status code: {status}"
        self.message_overlay.displayMessage(msg, True)

    def changeAcSleepTimeout(self, value: str) -> None:
        """Change system sleep timeout to given value"""
        minute = self.parse_time(value)
        status = power.change_setting_value('standby-timeout-ac', minute)
        if not status:
            return  # on success
        msg = f"Failed to change ac sleep timeout, status code: {status}"
        self.message_overlay.displayMessage(msg, True)

    def changeDcDisplayTimeout(self, value: str) -> None:
        """Change monitor timeout to given value"""
        minute = self.parse_time(value)
        status = power.change_setting_value('monitor-timeout-dc', minute)
        if not status:
            return  # on success
        msg = f"Failed to change dc display timeout, status code: {status}"
        self.message_overlay.displayMessage(msg, True)

    def changeDcSleepTimeout(self, value: str) -> None:
        """Change system sleep timeout to given value"""
        minute = self.parse_time(value)
        status = power.change_setting_value('standby-timeout-dc', minute)
        if not status:
            return  # on success
        msg = f"Failed to change dc sleep timeout, status code: {status}"
        self.message_overlay.displayMessage(msg, True)


# *================================================
# *              PLAN SETTINGS                    *
# *================================================

class PlanSettings(QFrame):
    def __init__(self, master: QWidget, parent: QStackedWidget, scheme_name: str, scheme_guid: str) -> None:
        super().__init__(parent)
        self._master = master
        self._parent = parent
        self.scheme_name = scheme_name
        self.scheme_guid = scheme_guid
        self.setupWidgets()
        self.setStyleSheet(styles.get("plansettings"))
        self.addSelf()

    def addSelf(self) -> None:
        """Add self to stacked widget"""
        self.__just_entered = True
        self._parent.addWidget(self)
        self._parent.setCurrentWidget(self)
        self._parent.currentChanged.connect(self.removeSelf)  # type: ignore

    def removeSelf(self) -> None:
        """Remove self from stacked widget on change"""
        if self.__just_entered:
            self.__just_entered = False
            return
        self._parent.removeWidget(self)
        self.deleteLater()  # delete this widget when changed

    def switchToMaster(self) -> None:
        """Switch to master widget"""
        self._parent.setCurrentWidget(self._master)

    def setupWidgets(self) -> None:
        """Set up the widgets for the settings screen"""
        top_label = QLabel(
            f"Change settings for the plan: {self.scheme_name}")
        top_label.setMargin(10)
        top_label.setObjectName("TopLabel")
        self.top_label = top_label

        self.message_overlay = MessageOverlay(self)
        comboboxes = DisplaySleepTimeout(
            self, self.scheme_guid, self.message_overlay)
        buttons = self.makeButtonsWidget()

        layout = QVBoxLayout(self)
        layout.addWidget(top_label)
        layout.addSpacing(3)
        layout.addWidget(comboboxes)
        layout.addSpacing(20)
        layout.addWidget(buttons)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        vertical_spacer = QSpacerItem(
            20, 20, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        layout.addSpacerItem(vertical_spacer)
        layout.addWidget(self.message_overlay)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def makeButtonsWidget(self) -> QWidget:
        """Make buttons widget and connect them to their corresponding functions.

        Add checkboxes to enable rename and delete buttons for default schemes
        """
        rename_button = InputButton("Change Scheme Name")
        rename_button.setPlaceholderText("Enter new scheme name")
        rename_button.setConfirmText("Change")
        duplicate_button = InputButton("Duplicate Scheme")
        duplicate_button.setPlaceholderText(
            "Enter destination guid - Optional")
        duplicate_button.setConfirmText("Duplicate")
        export_button = QPushButton("Export this Scheme")
        delete_button = QPushButton("Delete this Scheme")
        advance_settings_button = QPushButton("Open Advanced Settings")

        rename_button.connect(self.changeSchemeName)
        duplicate_button.connect(self.duplicateScheme)
        export_button.clicked.connect(self.exportScheme)  # type: ignore
        delete_button.clicked.connect(self.deleteScheme)  # type: ignore
        advance_settings_button.clicked.connect(  # type: ignore
            power.launch_advanced_settings)

        widget = QWidget(self)
        layout = QGridLayout(widget)
        layout.addWidget(rename_button, 0, 0)
        layout.addWidget(duplicate_button, 1, 0)
        layout.addWidget(export_button, 2, 0)
        layout.addWidget(delete_button, 3, 0)
        layout.addWidget(advance_settings_button, 4, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        widget.setLayout(layout)
        if self.scheme_guid not in power.DEFAULT_SCHEME_GUIDS:
            return widget

        rename_button.setDisabled(True)  # disable rename button
        delete_button.setDisabled(True)  # disable delete button
        # for default schemes and add checkboxes to enable them to make changes little harder
        # since these settings should not be changed recklessly or by mistake.
        rename_checkbox = QCheckBox(widget)
        delete_checkbox = QCheckBox(widget)
        # toggle widgets using checkboxes
        rename_checkbox.clicked.connect(  # type: ignore
            lambda: rename_button.setEnabled(True) if rename_checkbox.isChecked() \
            else rename_button.setDisabled(True)
        )
        delete_checkbox.clicked.connect(  # type: ignore
            lambda: delete_button.setEnabled(True) if delete_checkbox.isChecked() \
            else delete_button.setDisabled(True)
        )
        # add checkboxes to layout
        layout.addWidget(rename_checkbox, 0, 0,
                         Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(delete_checkbox, 3, 0,
                         Qt.AlignmentFlag.AlignLeft)
        # hide rename button's checkbox when not in the view
        rename_button.button.clicked.connect(  # type: ignore
            rename_checkbox.hide)
        rename_button.cancel_button.clicked.connect(  # type: ignore
            rename_checkbox.show)
        return widget

    def changeSchemeName(self, scheme_name: str) -> int:
        """Change the name of the current scheme"""
        if not power.re.fullmatch(r"^(?!\s)[A-Za-z0-9\s]{3,}(?!\s)$", scheme_name):
            msg = f"Invalid scheme name: {scheme_name!r}"
            self.message_overlay.displayMessage(msg, True)
            return 1    # as failed
        scheme_name = scheme_name.strip()  # remove whitespaces
        if status := power.change_name(self.scheme_guid, scheme_name):
            msg = f"Failed to change scheme name to {scheme_name!r}, status code: {status}"
            self.message_overlay.displayMessage(msg, True)
            return status
        msg = f"Changed scheme name {self.scheme_name!r} -> {scheme_name!r}"
        self.message_overlay.displayMessage(msg)
        self.top_label.setText(f"Change settings for the plan: {scheme_name}")
        self.scheme_name = scheme_name
        return status

    def duplicateScheme(self, destination_guid: str = '') -> int:
        """Duplicate the current scheme to destination guid"""
        if destination_guid and not power.re.match(power.GUID_PATTERN, destination_guid):
            msg = (f"Invalid scheme guid: {destination_guid}")
            self.message_overlay.displayMessage(msg, True)
            return 1  # as failed
        _, guid = power.duplicate_scheme(self.scheme_guid, destination_guid)
        msg = f"Duplicated {self.scheme_name!r} -> guid: {guid}"
        self.message_overlay.displayMessage(msg)
        return 0  # as success

    def exportScheme(self) -> None:
        """Export the current scheme to file"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, f"Save {self.scheme_name} Scheme",
            f"{self.scheme_name}.pow", "pow (*.pow)")

        if not filepath:
            return  # if no path selected
        if status := power.export_scheme(filepath, self.scheme_guid):
            msg = f"Failed to export scheme: {self.scheme_name!r}, status code: {status}"
            self.message_overlay.displayMessage(msg, True)
            return
        msg = f"Successively exported scheme: {self.scheme_name!r}"
        self.message_overlay.displayMessage(msg)

    def deleteScheme(self) -> None:
        """Delete the current scheme"""
        answer = QMessageBox.warning(
            self, "Are you sure you want to delete this plan?",
            "This plan can't be restored after you delete it.",
            QMessageBox.StandardButton.Cancel |
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Cancel
        )
        if answer == QMessageBox.StandardButton.Cancel:
            return  # on cancel
        if not (status := power.delete_scheme(self.scheme_guid)):
            return self.switchToMaster()   # on success
        msg = f"Failed to delete scheme: {self.scheme_name!r}, status code: {status}"
        self.message_overlay.displayMessage(msg, True)
