from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout, QWidget

import styles


class LoadingWidget(QFrame):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setupWidgets()
        self.setStyleSheet(styles.get("loading"))

    def setupWidgets(self) -> None:
        label = QLabel("<p align=center>Loading Packages...</p>")

        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)

        label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
