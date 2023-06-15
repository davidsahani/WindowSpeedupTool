from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (QApplication, QFrame, QGridLayout, QMainWindow,
                             QPushButton, QSizePolicy, QStackedWidget,
                             QVBoxLayout, QWidget)

import styles
from advanceoptions import AdvanceOptions
from driversbackup import DriversBackup
from poweroptions import PowerOptions
from systemcleaner import SystemCleaner
from systeminfo import SystemInfo
from systemrepair import SystemRepair
from windowservices import WindowServices
from windowsupdate import WindowsUpdate

WIDGETS = [
    ("System Info", SystemInfo),
    ("System Repair", SystemRepair),
    ("Power Options", PowerOptions),
    ("Drivers Backup", DriversBackup),
    ("System Cleaner", SystemCleaner),
    ("Windows Update", WindowsUpdate),
    ("Windows Services", WindowServices),
    ("Advance Options", AdvanceOptions)
]


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.widgets: dict[int, QWidget] = {}
        self.initializeUI()
        self.sidebar.setStyleSheet(styles.get("sidebar"))

    def initializeUI(self) -> None:
        self.setWindowTitle("Windows Speedup Tool")
        self.setWindowIcon(QIcon(r".\icons\thunder-bolt.png"))
        self.resize(788, 560)
        self.setupUI()
        self.show()

    def setupUI(self) -> None:
        """Setup widgets for main window"""
        self.stacked_widget = QStackedWidget(self)

        self.sidebar = self.makeSidebar()
        # Set first display widget
        button = self.sidebar.layout().itemAt(0).widget()
        self.setCurrentIndex(0, button)  # type: ignore
        self.sidebar.setSizePolicy(  # set sidebar size policy
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        main_widget = QWidget(self)
        layout = QGridLayout()
        layout.addWidget(self.sidebar, 0, 0)
        layout.addWidget(self.stacked_widget, 0, 1)
        layout.setContentsMargins(10, 10, 10, 0)
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

    def makeSidebar(self) -> QFrame:
        """Make sidebar widget"""
        frame = QFrame()
        layout = QVBoxLayout(frame)

        for idx, (name, _) in enumerate(WIDGETS):
            button = QPushButton(name)
            button.clicked.connect(  # type: ignore
                lambda _, i=idx, b=button:  # type: ignore
                self.setCurrentIndex(i, b)  # type: ignore
            )
            button.setCheckable(True)
            layout.addWidget(button)
        self.previous_button = button  # type: ignore

        layout.setAlignment(
            button, Qt.AlignmentFlag.AlignBottom)  # type: ignore
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeading)
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setLayout(layout)
        return frame

    def setCurrentIndex(self, idx: int, button: QPushButton) -> None:
        """Set current widget at the given index and update buttons."""
        widget = self.widgets.get(idx)
        if widget is None:
            _, cls = WIDGETS[idx]
            widget = cls(self.stacked_widget)
            self.widgets[idx] = widget
            self.stacked_widget.addWidget(widget)
        self.stacked_widget.setCurrentWidget(widget)
        if button is not self.previous_button:
            self.previous_button.setChecked(False)
            self.previous_button = button
        button.setChecked(True)


if __name__ == '__main__':
    import os
    import sys
    import qdarkstyle  # type: ignore
    os.chdir(os.path.dirname(__file__))

    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(  # type: ignore
        qt_api='pyqt6'))
    window = MainWindow()
    sys.exit(app.exec())
