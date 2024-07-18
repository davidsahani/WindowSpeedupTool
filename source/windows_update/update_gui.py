from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from window_services.services_thread import ServicesType


class UpdateGui(QFrame):
    def __init__(self, services: ServicesType, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.services = services
        self.setupWidgets()

    def setupWidgets(self) -> None:
        """Setup the widgets in layout."""
        layout = QVBoxLayout()
        layout.addWidget(self.createTopWidget())
        layout.addWidget(self.createCheckboxesGroupBox())
        layout.addWidget(self.createServicesGroupBox())
        layout.addWidget(self.createServiceButtonsWidget())
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def createTopWidget(self) -> QWidget:
        """Create the Top level widget."""
        update_label = QLabel("Windows Update")
        update_label.setObjectName("UpdateLabel")
        update_label.setContentsMargins(0, 1, 0, 10)

        self.update_icon_button = QPushButton()
        self.update_icon_button.setObjectName("UpdateIcon")

        self.status_label = QLabel("Status: Active")
        self.status_label.setObjectName("StatusLabel")

        self.toggle_update_button = QPushButton("Deactivate")

        widget = QWidget()
        layout = QGridLayout(widget)
        layout.addWidget(update_label, 0, 0, 1, 2)
        layout.addWidget(self.update_icon_button, 1, 0, 1, 1)
        layout.addWidget(self.status_label, 1, 1, 1, 1)
        layout.addWidget(self.toggle_update_button, 1, 2, 2, 1)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setAlignment(self.toggle_update_button,
                            Qt.AlignmentFlag.AlignRight)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)
        return widget

    def createCheckboxesGroupBox(self) -> QGroupBox:
        """Create automatic windows update and driver update checkboxes."""
        self.automatic_updates_checkbox = QCheckBox(
            "Automatic Windows Update"
        )
        self.automatic_driver_updates_checkbox = QCheckBox(
            "Automatic Drivers update during Windows update"
        )

        group_box = QGroupBox()
        layout = QVBoxLayout(group_box)
        layout.addWidget(self.automatic_updates_checkbox)
        layout.addWidget(self.automatic_driver_updates_checkbox)
        group_box.setLayout(layout)
        return group_box

    def createServicesGroupBox(self) -> QGroupBox:
        """Create group box for services status and state buttons."""
        group_box = QGroupBox()
        layout = QGridLayout(group_box)
        self.ins_dict: dict[str, tuple[QPushButton, QPushButton]] = {}

        for row, svc in enumerate(self.services):
            service_label = QLabel(svc.display_name)
            status_button = QPushButton("Start")
            state_button = QPushButton("Enable")
            self.ins_dict[svc.service_name] = status_button, state_button

            layout.addWidget(service_label, row, 0)
            layout.addWidget(status_button, row, 1)
            layout.addWidget(state_button, row, 2)

        layout.setAlignment(Qt.AlignmentFlag.AlignLeading)
        group_box.setLayout(layout)
        group_box.setSizePolicy(  # set group box size policy
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        return group_box

    def createServiceButtonsWidget(self) -> QWidget:
        """Create start, stop, enable and disable services buttons."""
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
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum
        )
        return widget
