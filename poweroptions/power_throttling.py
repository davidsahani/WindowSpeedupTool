import os
import re

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (QFileDialog, QFrame, QGridLayout, QGroupBox,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QVBoxLayout, QWidget)

from utils import power


class PowerThrottling(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setupWidgets()

    def setupWidgets(self) -> None:
        """Setup widgets in layout"""
        layout = QVBoxLayout()
        layout.addWidget(self.makeProgramsGroupBox())
        layout.setSpacing(1)
        layout.addWidget(self.makeProgramAddWidget())
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def makeProgramsGroupBox(self) -> QGroupBox:
        """Make a group box for program scheme buttons"""
        self.programs_ins: dict[str, tuple[QPushButton, QPushButton]] = {}
        layout = QGridLayout()

        programs = power.list_powerthrottling()
        for row, program in enumerate(programs):
            self.makeProgramButtons(row, layout, program)

        gbox = QGroupBox()
        gbox.setTitle("Power Throttling Disabled Apps")
        gbox.setLayout(layout)
        self.programs_layout = layout
        return gbox

    def makeProgramButtons(self, row: int, grid: QGridLayout, program: str) -> None:
        """Make buttons for program name and remove and add them to layout"""
        program_button = QPushButton(program)
        remove_button = QPushButton("✕")
        remove_button.clicked.connect(  # type: ignore
            lambda: self.removeApplication(program))
        program_button.setObjectName("ProgramButton")
        remove_button.setObjectName("RemoveButton")

        grid.addWidget(program_button, row, 0)
        grid.addWidget(remove_button, row, 1,
                       Qt.AlignmentFlag.AlignRight)
        self.programs_ins[program] = (program_button, remove_button)

    def makeProgramAddWidget(self) -> QWidget:
        """Make widget for adding program"""
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("Enter program name or path")

        file_button = QPushButton("Browse...")
        add_button = QPushButton("┿")
        file_button.clicked.connect(self.openFile)  # type: ignore
        add_button.clicked.connect(self.addApplication)  # type: ignore
        add_button.setObjectName("AddButton")

        self.warning_label = QLabel()
        self.warning_label.setObjectName("WarningLabel")

        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.addWidget(self.line_edit)
        layout.addWidget(file_button)
        layout.addWidget(add_button)
        layout.addWidget(self.warning_label)
        layout.setStretchFactor(self.warning_label, 1)
        layout.setContentsMargins(0, 6, 0, 0)
        self.line_edit.setMinimumWidth(300)
        widget.setLayout(layout)
        return widget

    def openFile(self) -> None:
        """Open program file"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open Program", "", "Programs (*.exe)")

        if not filepath:
            return  # if not selected
        self.line_edit.setText(filepath)

    def keyPressEvent(self, a0: QKeyEvent) -> None:
        """Handle line edit keyEvent"""
        if not self.line_edit.hasFocus():
            return
        if self.warning_label.text():
            self.warning_label.setText("")
        keys = (Qt.Key.Key_Return.value, Qt.Key.Key_Enter.value)
        if a0.key() not in keys:
            return
        self.addApplication()

    def addApplication(self) -> None:
        """Add program to programs' group-box and disable it's power throttling"""
        program = self.line_edit.text()
        if not program:
            return  # if no input
        if program in self.programs_ins:
            return  # if already in dict

        if self.ispath(program):
            if not os.path.splitext(program)[1] or program.endswith('.'):
                self.warning_label.setText("Invalid program filepath")
                return
            if not program.endswith('.exe'):
                self.warning_label.setText("Invalid executable")
                return
            if not os.path.isfile(program):
                self.warning_label.setText("File doesn't exist")
                return
        elif not self.is_program(program):
            self.warning_label.setText("Invalid program name")
            return

        self.warning_label.setText("")
        self.line_edit.clear()
        layout = self.programs_layout
        self.makeProgramButtons(layout.rowCount(), layout, program)
        self.update()  # update the window
        power.disable_powerthrottling(program)

    def removeApplication(self, program: str) -> None:
        """Add program from programs' group-box and reset it's power throttling"""
        b1, b2 = self.programs_ins[program]
        self.programs_layout.removeWidget(b1)
        self.programs_layout.removeWidget(b2)
        self.update()  # update the window
        del self.programs_ins[program]
        power.reset_powerthrottling(program)

    @staticmethod
    def is_program(name: str) -> bool:
        """Check if executable name is valid"""
        return re.match(r'([\w-])*\.exe$', name) is not None

    @staticmethod
    def ispath(filepath: str) -> bool:
        """Check if filepath is valid windows path"""
        pattern1 = r'^[a-zA-Z]:/(?:[^//:*?"<>|\r\n]+/)*[^//:*?"<>|\r\n]*$'
        pattern2 = r'^[a-zA-Z]:\\(?:[^\\/:*?"<>|\r\n]+\\)*[^\\/:*?"<>|\r\n]*$'
        if re.match(pattern1, filepath):
            return True
        return re.match(pattern2, filepath) is not None
