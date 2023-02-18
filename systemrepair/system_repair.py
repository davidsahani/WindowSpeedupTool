import psutil
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QComboBox, QFrame, QGridLayout, QGroupBox,
                             QPushButton, QScrollArea, QSizePolicy,
                             QVBoxLayout, QWidget)

import styles
from src.process_terminal import ProcessTerminal
from src.sizegrip import SizeGrip

SYSTEM_REPAIR_COMMANDS = [
    (
        "SFC /Scannow",
        "Scans integrity of all protected system files and repairs files with problems when possible."
    ),
    (
        "Dism /Online /Cleanup-Image /CheckHealth",
        "Checks whether the image has been flagged as corrupted " +
        "by a failed process and whether the corruption can be repaired."
    ),
    (
        "Dism /Online /Cleanup-Image /ScanHealth",
        "Scans the image for component store corruption."
    ),
    (
        "Dism /Online /Cleanup-Image /RestoreHealth",
        "Scans the image for component store corruption, and then performs repair operations automatically."
    )
]

DISK_REPAIR_COMMANDS = [
    (
        "Chkdsk",
        "Checks a disk and displays a status report."
    ),
    (
        "Chkdsk /c",
        "NTFS only: Skips checking of cycles within the folder structure."
    ),
    (
        "Chkdsk /b",
        "NTFS only: Re-evaluates bad clusters on the volume (implies /R)"
    ),
    (
        "Chkdsk /f",
        "Fixes errors on the disk."
    ),
    (
        "Chkdsk /r",
        "Locates bad sectors and recovers readable information (implies /F, when /scan not specified)."
    ),
    (
        "Chkdsk /r /c",
        "NTFS only: Locates bad sectors and recovers readable information " +
        "and skips checking of cycles within the folder structure."
    )
]

IMAGE_CLEANUP_COMMANDS = [
    (
        "Dism /Online /Cleanup-Image /AnalyzeComponentStore",
        "Create a report of the WinSxS component store."
    ),
    (
        "Dism /Online /Cleanup-Image /StartComponentCleanup",
        "Clean up the superseded components and reduce the size of the component store."
    ),
    (
        "Dism /Online /Cleanup-Image /StartComponentCleanup /ResetBase",
        "Reset the base of superseded components, which can further reduce the component store size."
    ),
    (
        "Dism /Online /Cleanup-Image /revertpendingactions",
        "Revert any windows update pending actions."
    )
]


class SystemRepair(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._parent = parent
        self.setupWidgets()
        self.setStyleSheet(styles.get("power"))

    def setupWidgets(self) -> None:
        """Setup the widgets in scroll widget"""
        widget = QWidget()
        vlayout = QVBoxLayout()
        vlayout.addWidget(self.createSystemRepairGroupBox())
        vlayout.addWidget(self.createImageCleanUpGroupBox())
        vlayout.addWidget(self.createDiskRepairGroupBox())
        vlayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        vlayout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(vlayout)

        scroll_widget = QScrollArea(self)
        scroll_widget.setWidgetResizable(True)
        scroll_widget.setFrameShape(QFrame.Shape.NoFrame)
        scroll_widget.setWidget(widget)
        scroll_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.process_terminal = ProcessTerminal(self)
        size_grip = SizeGrip(self, self.process_terminal)
        size_grip.hide()              # hide initially
        self.process_terminal.hide()  # hide initially

        layout = QVBoxLayout()
        layout.addWidget(scroll_widget)
        layout.addWidget(size_grip)
        layout.addWidget(self.process_terminal)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def createSystemRepairGroupBox(self) -> QGroupBox:
        widget = QGroupBox(self)
        widget.setTitle("System Repair Commands")

        layout = QVBoxLayout(self)
        for command, description in SYSTEM_REPAIR_COMMANDS:
            button = QPushButton(f"Run {command}")
            button.setToolTip(description)
            button.clicked.connect(  # type: ignore
                lambda _, x=command:  # type: ignore
                self.process_terminal.runCommand(x)  # type: ignore
            )
            layout.addWidget(button)

        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        widget.setLayout(layout)
        return widget

    def createImageCleanUpGroupBox(self) -> QGroupBox:
        widget = QGroupBox(self)
        widget.setTitle("Image Cleanup Commands")

        layout = QVBoxLayout(self)
        for command, description in IMAGE_CLEANUP_COMMANDS:
            button = QPushButton(f"Run {command}")
            button.setToolTip(description)
            button.clicked.connect(  # type: ignore
                lambda _, x=command:  # type: ignore
                self.process_terminal.runCommand(x)  # type: ignore
            )
            layout.addWidget(button)

        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        widget.setLayout(layout)
        return widget

    def createDiskRepairGroupBox(self) -> QGroupBox:
        widget = QGroupBox(self)
        widget.setTitle("Disk Repair Commands")
        layout = QGridLayout(self)

        row, column = 0, 0
        for row, (command, description) in enumerate(DISK_REPAIR_COMMANDS):
            button = QPushButton(f"Run {command}")
            button.setToolTip(description)
            button.clicked.connect(  # type: ignore
                lambda _, x=command:  # type: ignore
                self.process_terminal.runCommand(x)  # type: ignore
            )
            layout.addWidget(button, row // 2, column)
            column = 0 if column else 1  # flip-flop

        button1 = QPushButton("Run chkdsk c:\\")
        selection_box1 = QComboBox(self)
        button2 = QPushButton("Run chkdsk /f volume:c:\\")
        selection_box2 = QComboBox(self)

        selection_box1.currentTextChanged.connect(  # type: ignore
            lambda text: button1.setText(  # type: ignore
                f"Run chkdsk {text.lower()}")  # type: ignore
        )
        selection_box2.currentTextChanged.connect(  # type: ignore
            lambda text: button2.setText(  # type: ignore
                f"Run chkdsk /f volume:{text.lower()}")  # type: ignore
        )
        button1.clicked.connect(  # type: ignore
            lambda: self.process_terminal.runCommand(
                f"chkdsk {selection_box1.currentText().lower()}")
        )
        button2.clicked.connect(  # type: ignore
            lambda: self.process_terminal.runCommand(
                f"chkdsk volume:{selection_box2.currentText().lower()} /f")
        )
        partitions = self.partitions()
        selection_box1.addItems(partitions)
        selection_box2.addItems(partitions)

        layout.addWidget(button1, row + 1, 0)
        layout.addWidget(selection_box1, row + 1, 1)
        layout.addWidget(button2, row + 2, 0)
        layout.addWidget(selection_box2, row + 2, 1)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        widget.setLayout(layout)
        return widget

    def partitions(self) -> list[str]:
        """Return list of all disk partitions"""
        return [partition.device for partition in
                psutil.disk_partitions(all=False)]
