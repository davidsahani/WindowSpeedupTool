import functools
import os
import subprocess
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from advanceoptions import AdvanceOptions
from drivers_backup import DriversBackup
from power_options import PowerOptions
from system_cleaner import SystemCleaner
from system_info import SystemInfo
from system_repair import SystemRepair
from utils import config, styles, threads
from widgets.stacked_widget import StackedWidget
from window_services import WindowServices
from windows_update import WindowsUpdate

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
    def __init__(self, cls_name: str | None = None) -> None:
        super().__init__()
        self.initializeUI(cls_name)
        self.resize(788, 560)
        self.show()

    def initializeUI(self, cls_name: str | None) -> None:
        self.setWindowIcon(QIcon("icons\\thunder-bolt.png"))

        name, cls = next(
            ((name, cls) for name, cls in WIDGETS if cls.__name__
             == cls_name), (None, None)) if cls_name else (None, None)

        if cls is not None:
            result = threads.Result.from_command(["whoami"])
            self.setWindowTitle(f"{name} - user: {result.value}")
            self.setupMainWidget(cls)
        else:
            self.setupMainUI()
            self.setWindowTitle("Windows Speedup Tool")
            self.sidebar.setStyleSheet(styles.get("sidebar"))

    def setupMainWidget(self, cls: type) -> None:
        """Setup the widget for main window."""
        stacked_widget = StackedWidget(self)
        widget = cls(stacked_widget)
        stacked_widget.addWidget(widget)
        stacked_widget.setCurrentWidget(widget)
        self.setCentralWidget(stacked_widget)

    def setupMainUI(self) -> None:
        """Setup the widgets for main window."""
        self.stacked_widget = StackedWidget(self)

        self.sidebar = self.createSidebar()
        self.sidebar.setSizePolicy(  # set sidebar size policy
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        # set first display widget.
        self.setCurrentWidget(SystemInfo)
        # set first button selected.
        layout = self.sidebar.layout()
        item = layout.itemAt(0) if layout else None
        button = item.widget() if item else None
        if button and isinstance(button, QPushButton):
            self.setCurrentButtonSelected(button)

        main_widget = QWidget(self)
        layout = QGridLayout(main_widget)
        layout.addWidget(self.sidebar, 0, 0)
        layout.addWidget(self.stacked_widget, 0, 1)
        layout.setContentsMargins(10, 10, 10, 0)
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

    def createSidebar(self) -> QFrame:
        """Create the sidebar widget."""
        frame = QFrame()
        layout = QVBoxLayout(frame)
        # instantiate variable to ignore unbound variable linter warning.
        button: QPushButton = None  # type: ignore - button will be reassigned

        for name, _class in WIDGETS:
            button = QPushButton(name)
            button.clicked.connect(
                functools.partial(self.handleButtonClick, _class, button)
            )
            button.setCheckable(True)
            layout.addWidget(button)

        self.previous_button = button
        layout.setAlignment(button, Qt.AlignmentFlag.AlignBottom)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeading)
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setLayout(layout)
        return frame

    def handleButtonClick(self, _class: type, button: QPushButton):
        self.setCurrentWidget(_class)
        self.setCurrentButtonSelected(button)

    def setCurrentWidget(self, cls: type) -> None:
        """Set current widget by given class."""
        widget = self.stacked_widget.widgetName(cls.__name__)
        if widget is None:
            if cls.__name__ == AdvanceOptions.__name__:
                if self.launchAdvanceOptions():
                    return
            widget = cls(self.stacked_widget)
            self.stacked_widget.addWidget(widget)
        self.stacked_widget.setCurrentWidget(widget)

    def setCurrentButtonSelected(self, button: QPushButton) -> None:
        """Set current button selected and previous button unselected."""
        if button is not self.previous_button:
            self.previous_button.setChecked(False)
            self.previous_button = button
        button.setChecked(True)

    def launchAdvanceOptions(self) -> bool:
        """Launch Advance Options with nsudo."""
        nsudo = os.path.join(config.PROJECT_DIR, "bin", "nsudo.exe")
        if not os.path.exists(nsudo):
            QMessageBox.warning(
                self.sidebar,
                "NSudo Not Found",
                f"NSudo must be in: {os.path.dirname(nsudo)}.\n" +
                "Download it from: https://github.com/M2TeamArchived/NSudo/releases\n" +
                "and place it in the specified directory if you're unable to locate it."
            )
            return False

        main_exe = os.path.join(config.PROJECT_DIR, "WindowSpeedupTool.exe")

        if os.path.exists(main_exe):
            subprocess.call(
                [nsudo, "-U:T", "-P:E", main_exe, AdvanceOptions.__name__]
            )
            return True
        return False


if __name__ == '__main__':
    import qdarkstyle  # type: ignore[no-stub]
    os.chdir(os.path.dirname(__file__))

    app = QApplication(sys.argv)
    app.setStyleSheet(
        qdarkstyle.load_stylesheet(qt_api='pyqt6')  # type: ignore[attr]
    )
    window = MainWindow(sys.argv[1] if len(sys.argv) == 2 else None)
    sys.exit(app.exec())
