import json
import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QFrame, QGridLayout, QLabel, QPushButton,
                             QSizePolicy, QSpacerItem, QStackedWidget, QWidget)

import styles
from utils import config, service
from widgets.overlay import MessageOverlay


class ServicesList(QWidget):
    def __init__(self, parent: QWidget,
                 specific_config: str, normal_svc_config: str, message_overlay: MessageOverlay) -> None:
        super().__init__(parent)
        self.specific_config = specific_config
        self.normal_svc_config = normal_svc_config
        self.message_overlay = message_overlay
        self.normal_services = config.load(normal_svc_config)
        self.makeWidgets()

    def makeWidgets(self) -> None:
        """Make the widgets and setup the layout"""
        with open(os.path.join(config.DEFAULT_DIR, self.specific_config)) as file:
            self.services = json.load(file)

        layout = QGridLayout()
        for row, key in enumerate(self.services):
            label = QLabel(key)
            enable_button = QPushButton("Enable")
            disable_button = QPushButton("Disable")
            enable_button.clicked.connect(  # type: ignore
                lambda _, x=key: self.enableServices(x)  # type: ignore
            )
            disable_button.clicked.connect(  # type: ignore
                lambda _, x=key: self.disableServices(x)  # type: ignore
            )
            layout.addWidget(label, row, 0)
            layout.addWidget(enable_button, row, 1)
            layout.addWidget(disable_button, row, 2)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def enableServices(self, key: str) -> None:
        """Enable the windows services"""
        service_names = self.services[key]
        failed_services: list[str] = []
        for service_name in service_names:
            startup_type = self.normal_services[service_name]
            if not service.set_startup_type(service_name, startup_type):
                continue  # on success
            failed_services.append(service_name)

        if not failed_services:
            msg = f"Enabled: {key}"
        elif len(failed_services) == 1:
            msg = f"failed to enable service: {failed_services[0]}"
        else:
            msg = f"failed to enable services: {failed_services}"
        self.message_overlay.displayMessage(msg, bool(failed_services))

    def disableServices(self, key: str) -> None:
        """Disable the windows services"""
        service_names = self.services[key]
        failed_services: list[str] = []
        for service_name in service_names:
            if not service.set_startup_type(service_name, 'disabled'):
                continue  # on success
            failed_services.append(service_name)

        if not failed_services:
            msg = f"Disabled: {key}"
        elif len(failed_services) == 1:
            msg = f"failed to disable service: {failed_services[0]}"
        else:
            msg = f"failed to disable services: {failed_services}"
        self.message_overlay.displayMessage(msg, bool(failed_services))


class NormalSpecificServices(QFrame):
    def __init__(self, master: QWidget, parent: QStackedWidget, specific_config: str, normal_svc_config: str) -> None:
        super().__init__(parent)
        self._master = master
        self._parent = parent
        self.specific_config = specific_config
        self.normal_svc_config = normal_svc_config
        self.setupWidgets()
        self.addSelf()
        self.setStyleSheet(styles.get("specificservices"))

    def addSelf(self) -> None:
        """Add self to stacked widget and remove on change"""
        self.__just_entered = True
        self._parent.addWidget(self)
        self._parent.setCurrentWidget(self)
        self._parent.currentChanged.connect(self.removeSelf)  # type: ignore

    def removeSelf(self) -> None:
        """Remove self from stacked widget"""
        if self.__just_entered:
            self.__just_entered = False
            return
        self._parent.removeWidget(self)
        self.deleteLater()  # delete this widget when changed

    def switchToMaster(self) -> None:
        """Switch to master widget"""
        self._parent.setCurrentWidget(self._master)

    def setupWidgets(self) -> None:
        """Setup the widgets in layout"""
        label = QLabel("<p align=center>Normal Specific Services</p>")
        label.setObjectName("TopLabel")
        message_overlay = MessageOverlay(self)
        widget = ServicesList(self, self.specific_config,
                              self.normal_svc_config, message_overlay)

        layout = QGridLayout()
        layout.addWidget(label)
        layout.addWidget(widget)
        vertical_spacer = QSpacerItem(
            20, 20, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        layout.addItem(vertical_spacer)
        layout.addWidget(message_overlay)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
