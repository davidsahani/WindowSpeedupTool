from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)


class CleanerGui(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setupWidgets()

    def setupWidgets(self) -> None:
        """Setup the widgets in layout."""
        self.circle_button = QPushButton()
        self.circle_button.setObjectName("CircleButton")

        self.clean_button = QPushButton("Clean Junk Files")
        self.clean_button.setObjectName("CleanButton")

        self.clean_event_logs_checkbox = QCheckBox()
        self.clean_windows_update_checkbox = QCheckBox()
        self.clean_event_logs_checkbox.setChecked(True)

        self.clean_event_logs_button = QPushButton("Clean Event Logs")
        self.clean_windows_update_button = QPushButton("Clean Windows Updates")

        layout = QGridLayout()
        layout.addWidget(self.clean_event_logs_checkbox, 0, 0)
        layout.addWidget(self.clean_event_logs_button, 0, 1)
        layout.addWidget(self.clean_windows_update_checkbox, 1, 0)
        layout.addWidget(self.clean_windows_update_button, 1, 1)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeading)
        layout.setHorizontalSpacing(0)
        layout.setVerticalSpacing(5)

        spacer = QSpacerItem(  # spacer item for extra spacing
            20, 10, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed
        )

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.circle_button)
        main_layout.addSpacerItem(spacer)
        main_layout.addWidget(self.clean_button)
        main_layout.addSpacerItem(spacer)
        main_layout.addLayout(layout)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(main_layout)
