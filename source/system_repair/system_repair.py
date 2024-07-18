import functools
import subprocess
from typing import Sequence

import psutil
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from utils import config, styles

from .commands import (
    DISK_REPAIR_COMMANDS,
    IMAGE_CLEANUP_COMMANDS,
    SYSTEM_REPAIR_COMMANDS,
)


class SystemRepair(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setupWidgets()
        self.setStyleSheet(styles.get("power") + styles.get("sysinfo"))

    def setupWidgets(self) -> None:
        """Setup the widgets in layout."""
        layout = QVBoxLayout()

        layout.addWidget(self.createCommandsGroupBox(
            "System Repair Commands", SYSTEM_REPAIR_COMMANDS)
        )
        layout.addWidget(self.createCommandsGroupBox(
            "Image Cleanup Commands", IMAGE_CLEANUP_COMMANDS)
        )
        layout.addWidget(self.createDiskRepairGroupBox())

        main_widget = QWidget()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_widget.setLayout(layout)

        scroll_widget = QScrollArea(self)
        scroll_widget.setFrameShape(QFrame.Shape.NoFrame)
        scroll_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        scroll_widget.setWidget(main_widget)
        scroll_widget.setWidgetResizable(True)

        scroll_layout = QVBoxLayout()
        scroll_layout.addWidget(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(scroll_layout)

    def createCommandsGroupBox(self, title: str, commands: Sequence[tuple[str, str]]) -> QGroupBox:
        """Create group box with commands."""
        layout = QGridLayout()

        for row, (command, description) in enumerate(commands):
            run_callback = functools.partial(self.runCommand, command)

            button = QPushButton(command)
            button.setToolTip(description)
            button.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
            )
            button.clicked.connect(run_callback)

            run_button = QPushButton("➣")
            run_button.setToolTip("Run command in console window")
            run_button.setMinimumWidth(42)
            run_button.clicked.connect(run_callback)

            copy_button = QPushButton()
            copy_button.setObjectName("CopyButton")
            copy_button.setToolTip("Copy command to clipboard")
            copy_button.clicked.connect(
                functools.partial(self.copyTextToClipboard, command)
            )

            layout.addWidget(button, row, 0)
            layout.addWidget(run_button, row, 1)
            layout.addWidget(copy_button, row, 2)

        group_box = QGroupBox()
        group_box.setTitle(title)
        group_box.setLayout(layout)
        return group_box

    def createDiskRepairGroupBox(self) -> QGroupBox:
        """Create group box with disk repair commands."""
        group_box = QGroupBox()
        group_box.setTitle("Disk Repair Commands")

        first_button = QPushButton(DISK_REPAIR_COMMANDS[0][0])
        first_button.setToolTip(DISK_REPAIR_COMMANDS[0][1])
        first_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        first_button.clicked.connect(
            lambda: self.runCommand(first_button.text())
        )

        first_flags_selection_box = QComboBox()
        first_flags_selection_box.addItems(list(
            map(lambda x: x[0].removeprefix("Chkdsk").lstrip() or "flags", DISK_REPAIR_COMMANDS))
        )
        first_flags_selection_box.currentTextChanged.connect(lambda text: (  # type: ignore[unknown]
            first_button.setText(
                f"Chkdsk {text.removesuffix("flags")}"  # type: ignore[attr]
            ),
            first_button.setToolTip(
                DISK_REPAIR_COMMANDS[first_flags_selection_box.currentIndex()][1]
            )
        ))

        first_run_button = QPushButton("➣")
        first_run_button.setToolTip("Run command in console window")
        first_run_button.setMinimumWidth(42)
        first_run_button.clicked.connect(
            lambda: self.runCommand(first_button.text())
        )

        first_copy_button = QPushButton()
        first_copy_button.setObjectName("CopyButton")
        first_copy_button.setToolTip("Copy command to clipboard")
        first_copy_button.clicked.connect(
            lambda: self.copyTextToClipboard(first_button.text())
        )

        partitions = self.partitions()
        selected_partition = (partitions or [""])[0].removesuffix("\\")

        second_button = QPushButton(f"Chkdsk {selected_partition}")
        second_button.setToolTip(DISK_REPAIR_COMMANDS[0][1])
        second_button.clicked.connect(
            lambda: self.runCommand(second_button.text())
        )

        partition_selection_box = QComboBox()
        partition_selection_box.setMinimumWidth(50)
        partition_selection_box.addItems(partitions)
        partition_selection_box.setToolTip("Select disk to repair")
        partition_selection_box.currentTextChanged.connect(lambda text: (  # type: ignore[unknown]
            second_button.setText(
                f"Chkdsk {text.removesuffix("\\")} {  # type: ignore[attr]
                    second_flags_selection_box.currentText().removesuffix("flags")
                }"
            ),
            second_button.setToolTip(
                DISK_REPAIR_COMMANDS[second_flags_selection_box.currentIndex()][1]
            )
        ))

        second_flags_selection_box = QComboBox()
        second_flags_selection_box.addItems(list(
            map(lambda x: x[0].removeprefix("Chkdsk").lstrip() or "flags", DISK_REPAIR_COMMANDS))
        )
        second_flags_selection_box.currentTextChanged.connect(lambda text: (  # type: ignore[unknown]
            second_button.setText(
                f"Chkdsk {partition_selection_box.currentText().removesuffix("\\").lower()} {
                    text.removesuffix("flags")}"  # type: ignore[attr]
            ),
            second_button.setToolTip(
                DISK_REPAIR_COMMANDS[second_flags_selection_box.currentIndex()][1]
            )
        ))

        second_run_button = QPushButton("➣")
        second_run_button.setToolTip("Run command in console window")
        second_run_button.setMinimumWidth(42)
        second_run_button.clicked.connect(
            lambda: self.runCommand(second_button.text())
        )

        second_copy_button = QPushButton()
        second_copy_button.setObjectName("CopyButton")
        second_copy_button.setToolTip("Copy command to clipboard")
        second_copy_button.clicked.connect(
            lambda: self.copyTextToClipboard(second_button.text())
        )

        layout = QGridLayout()
        layout.addWidget(first_button, 0, 0)
        layout.addWidget(first_flags_selection_box, 0, 1, 1, 2)
        layout.addWidget(first_run_button, 0, 3)
        layout.addWidget(first_copy_button, 0, 4)

        layout.addWidget(second_button, 1, 0)
        layout.addWidget(partition_selection_box, 1, 1)
        layout.addWidget(second_flags_selection_box, 1, 2)
        layout.addWidget(second_run_button, 1, 3)
        layout.addWidget(second_copy_button, 1, 4)
        group_box.setLayout(layout)
        return group_box

    def copyTextToClipboard(self, text: str) -> None:
        """Copy text to the clipboard."""
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            return clipboard.setText(text)

        QMessageBox.critical(
            self, "Clipboard Error",
            "Failed to copy text to the clipboard.\
            \nPlease try again.",
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Ok
        )

    def runCommand(self, command: str) -> None:
        """Run the command in a new cmd window."""
        process = subprocess.Popen(
            ["start", "cmd", "/k", command], shell=True,
            cwd=config.PROJECT_DIR,  # shell directory.
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        if process.wait() == 0:
            return  # on success.

        error = process.stderr or process.stdout
        QMessageBox.critical(
            self, "Command Run Error",
            error.read().decode() if error else
            f"Failed to run command: {command}",
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Ok
        )

    @staticmethod
    def partitions() -> list[str]:
        """Return list of all disk partitions."""
        return [partition.device for partition in
                psutil.disk_partitions(all=False)]
