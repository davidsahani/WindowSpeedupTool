from typing import OrderedDict

from PyQt6.QtCore import QEvent, QPoint, Qt
from PyQt6.QtGui import QFontMetrics, QPainter
from PyQt6.QtWidgets import (QApplication, QFrame, QGridLayout, QGroupBox,
                             QLabel, QPushButton, QScrollArea, QSizePolicy,
                             QVBoxLayout, QWidget)

import styles

from . import sysinfo


class LineSpacingLabel(QLabel):
    def paintEvent(self, a0: QEvent) -> None:
        painter = QPainter(self)
        metrics = QFontMetrics(self.font())
        line_height = metrics.height() * 1.5  # adjust the line spacing here
        y = 0
        for line in self.text().splitlines():
            painter.drawText(QPoint(0, int(y) + metrics.ascent()), line)
            y += line_height
        painter.end()

        # Adjust widget size respect to line spacing
        height = y + metrics.descent() - 6.5
        self.setFixedHeight(int(height))


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
        gpus = self.makeGroupWidget(sysinfo.gpus())
        rams = self.makeGroupWidget(sysinfo.rams())
        disks = self.makeGroupWidget(sysinfo.disks())
        net_adapters = self.makeGroupWidget(sysinfo.net_adapters())
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

    def makeGroupWidget(self, values: list[tuple[str, str | int]] |
                        OrderedDict[str, list[tuple[str, str]]]) -> QGroupBox:
        """Make group widget for values"""
        if isinstance(values, list):
            text = '\n'.join((f"{name}: {value}" for name, value in values))
        elif len(values) == 1:
            text = '\n'.join(
                (f"{name}: {value}" for name, value in list(values.values())[0]))
        else:
            text = ''
            for _values in values.values():
                text += '\n'.join((f"{name}: {value}" for name,
                                  value in _values))
                text += '\n\n'
            text = text.rstrip('\n')
        label = LineSpacingLabel(text)

        copy_button = QPushButton()
        copy_button.setToolTip("copy")
        copy_button.setObjectName("CopyButton")
        copy_button.clicked.connect(  # type: ignore
            lambda: self.copyTextToClipboard(text))

        layout = QGridLayout()
        layout.addWidget(label, 0, 0)
        layout.addWidget(copy_button, 0, 1, Qt.AlignmentFlag.AlignTop
                         | Qt.AlignmentFlag.AlignRight)
        gbox = QGroupBox()
        gbox.setLayout(layout)
        return gbox

    def copyTextToClipboard(self, text: str) -> None:
        """Copy text to clipboard."""
        QApplication.clipboard().setText(text)
