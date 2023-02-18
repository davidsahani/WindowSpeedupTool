from typing import OrderedDict

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QApplication, QFrame, QGridLayout, QGroupBox,
                             QLabel, QPushButton, QScrollArea, QSizePolicy,
                             QVBoxLayout, QWidget)

import styles

from . import sysinfo


class SystemInfo(QFrame):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setupWidgets()
        self.setStyleSheet(styles.get("sysinfo"))

    def setupWidgets(self) -> None:
        """Setup widgets in scroll widget"""
        widget = self.makeWidget()
        scroll_widget = QScrollArea(self)
        scroll_widget.setWidgetResizable(True)
        scroll_widget.setFrameShape(QFrame.Shape.NoFrame)
        scroll_widget.setWidget(widget)
        scroll_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout()
        layout.addWidget(scroll_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def makeWidget(self) -> QWidget:
        """Make main widget for systeminfo"""
        processor = self.makeGroupWidget(sysinfo.processor())
        gpus = self.makeGroupWidget_(sysinfo.gpus())
        rams = self.makeGroupWidget_(sysinfo.rams())
        disks = self.makeGroupWidget_(sysinfo.disks())
        net_adapters = self.makeGroupWidget_(sysinfo.net_adapters())
        motherboard = self.makeGroupWidget(sysinfo.motherboard())
        os = self.makeGroupWidget(sysinfo.os_info())  # type: ignore

        processor.setTitle("Processor")
        gpus.setTitle("Gpu")
        rams.setTitle("Ram")
        disks.setTitle("Disk")
        net_adapters.setTitle("Network Adapter")
        motherboard.setTitle("Motherboard")
        os.setTitle("Operating System")

        widget = QWidget(self)
        layout = QVBoxLayout(self)
        layout.addWidget(processor)
        layout.addWidget(gpus)
        layout.addWidget(rams)
        layout.addWidget(disks)
        layout.addWidget(net_adapters)
        layout.addWidget(motherboard)
        layout.addWidget(os)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)
        return widget

    def makeGroupWidget(self, values: list[tuple[str, str | int]]) -> QGroupBox:
        """Make group widget for values"""
        layout = QGridLayout()
        copy_button = QPushButton()
        copy_button.setToolTip("copy")
        copy_button.setObjectName("CopyButton")
        copy_button.clicked.connect(  # type: ignore
            lambda: self.copyValuesToClipboard(values))
        layout.addWidget(copy_button, 0, 1, Qt.AlignmentFlag.AlignRight)

        for row, (name, value) in enumerate(values):
            label = QLabel(f"{name}: {value}")
            layout.addWidget(label, row, 0)

        gbox = QGroupBox()
        gbox.setLayout(layout)
        return gbox

    def makeGroupWidget_(self, values: OrderedDict[str, list[tuple[str, str]]]) -> QGroupBox:
        """Make group widget for keys-values"""
        if len(values) == 1:
            return self.makeGroupWidget(
                list(values.values())[0]  # type: ignore
            )
        layout = QGridLayout()
        copy_button = QPushButton()
        copy_button.setToolTip("copy")
        copy_button.setObjectName("CopyButton")
        copy_button.clicked.connect(  # type: ignore
            lambda: self.copyKeysValuesToClipboard(values))
        layout.addWidget(copy_button, 0, 1, Qt.AlignmentFlag.AlignRight)

        row = 0
        for key, _values in values.items():
            layout.addWidget(QLabel(f"{key}"), row, 0)
            row += 1
            for name, value in _values:
                layout.addWidget(QLabel(f"\t{name}: {value}"), row, 0)
                row += 1

        gbox = QGroupBox()
        gbox.setLayout(layout)
        return gbox

    def copyValuesToClipboard(self, values: list[tuple[str, str | int]]) -> None:
        """Copy values to clipboard."""
        text = '\n'.join((f"{name}: {value}" for name, value in values))
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

    def copyKeysValuesToClipboard(self, values: OrderedDict[str, list[tuple[str, str]]]) -> None:
        """Copy key-values to the clipboard."""
        if len(values) == 1:
            text = '\n'.join(
                (f"{name}: {value}" for name, value in values.values()))
        else:
            text = ""
            for key, _values in values.items():
                text += f"{key}\n"
                for name, value in _values:
                    text += f"\t{name}: {value}\n"

        clipboard = QApplication.clipboard()
        clipboard.setText(text)
