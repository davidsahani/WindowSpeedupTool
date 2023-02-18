from collections import OrderedDict
from typing import Iterable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QCheckBox, QFrame, QGridLayout, QGroupBox,
                             QHBoxLayout, QLabel, QPushButton, QSizePolicy,
                             QVBoxLayout, QWidget)

import styles
from utils import service


class UpdateGui(QFrame):
    def __init__(self, parent: QWidget, service_names: Iterable[str]) -> None:
        super().__init__(parent)
        self.services_names = service_names
        self.setupWidgets()
        self.setStyleSheet(styles.get("windowsupdate"))

    def setupWidgets(self) -> None:
        """Setup widgets in layout"""
        layout = QVBoxLayout()
        layout.addWidget(self.makeTopWidget())
        layout.addWidget(self.makeCheckboxesGroupBox())
        layout.addWidget(self.makeServicesGroupBox())
        layout.addWidget(self.makeButtonsWidget())
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def makeTopWidget(self) -> QWidget:
        """Make Top level widget"""
        update_label = QLabel("Windows Update")
        update_icon = QPushButton()
        self.status_label = QLabel("Status: Active")
        update_label.setObjectName("UpdateLabel")
        update_icon.setObjectName("UpdateIcon")
        self.status_label.setObjectName("StatusLabel")
        self.toggle_update_button = QPushButton("Deactivate")

        widget = QWidget()
        layout = QGridLayout(widget)
        layout.addWidget(update_label, 0, 0, 1, 2)
        layout.addWidget(update_icon, 1, 0, 1, 1)
        layout.addWidget(self.status_label, 1, 1, 1, 1)
        layout.addWidget(self.toggle_update_button, 1, 2, 2, 1)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        update_label.setContentsMargins(0, 1, 0, 10)
        layout.setAlignment(self.toggle_update_button,
                            Qt.AlignmentFlag.AlignRight)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)
        return widget

    def makeCheckboxesGroupBox(self) -> QGroupBox:
        """Make automatic windows update and driver update checkboxes"""
        self.automatic_updates_checkbox = QCheckBox(
            "Automatic Windows Updates")
        self.automatic_driver_updates_checkbox = QCheckBox(
            "Automatic Drivers update during Windows updates")

        group_box = QGroupBox()
        layout = QVBoxLayout(group_box)
        layout.addWidget(self.automatic_updates_checkbox)
        layout.addWidget(self.automatic_driver_updates_checkbox)
        group_box.setLayout(layout)
        return group_box

    def makeServicesGroupBox(self) -> QGroupBox:
        """Make services group box"""
        group_box = QGroupBox()
        layout = QGridLayout(group_box)
        self.ins_dict: OrderedDict[
            str, tuple[QPushButton, QPushButton]] = OrderedDict()

        for row, service_name in enumerate(self.services_names):
            display_name = service.display_name(service_name)
            service_label = QLabel(display_name)
            toggle_status_button = QPushButton("Start")
            toggle_state_button = QPushButton("Enable")
            self.ins_dict[service_name] = toggle_status_button, toggle_state_button

            layout.addWidget(service_label, row, 0)
            layout.addWidget(toggle_status_button, row, 1)
            layout.addWidget(toggle_state_button, row, 2)

        layout.setAlignment(Qt.AlignmentFlag.AlignLeading)
        group_box.setLayout(layout)
        group_box.setSizePolicy(  # set group box size policy
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        return group_box

    def makeButtonsWidget(self) -> QWidget:
        """Make services start/stop/enable/disable buttons"""
        self.start_services_button = QPushButton("Start Services")
        self.stop_services_button = QPushButton("Stop Services")
        self.enable_services_button = QPushButton("Enable Services")
        self.disable_services_button = QPushButton("Disable Services")

        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.addWidget(self.start_services_button)
        layout.addWidget(self.stop_services_button)
        layout.addWidget(self.enable_services_button)
        layout.addWidget(self.disable_services_button)
        widget.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setSizePolicy(  # set widget size policy
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        return widget
