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
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        widget_data = [
            ("Processor", self.formatText(sysinfo.processor())),
            ("Gpu", self.formatTextList(sysinfo.gpus())),
            ("Ram", self.formatTextList(sysinfo.rams())),
            ("Disk", self.formatTextList(sysinfo.disks())),
            ("Network Adapter", self.formatTextList(sysinfo.net_adapters())),
            ("Motherboard", self.formatText(sysinfo.motherboard())),
            ("Operating System", self.formatText(
                sysinfo.os_info()))  # type: ignore
        ]

        for title, data in widget_data:
            group_widget = self.makeGroupTextWidget(data)
            group_widget.setTitle(title)
            layout.addWidget(group_widget)

        widget.setLayout(layout)
        return widget

    @staticmethod
    def formatText(values: list[tuple[str, str | int]]) -> str:
        """Format text for group widget"""
        return '\n'.join((f"{name}: {value}" for name, value in values))

    @staticmethod
    def formatTextList(values: list[list[tuple[str, str]]]) -> str:
        """Format text for group widget"""
        res: list[str] = []
        for _values in values:
            res.append(
                '\n'.join((f"{name}: {value}" for name, value in _values)))
            res.append('\n\n')
        res.pop()  # remove last '\n'
        return ''.join(res)

    def makeGroupTextWidget(self, text: str) -> QGroupBox:
        """Make Group widget with specified text."""
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
        """Copy text to the clipboard."""
        QApplication.clipboard().setText(text)
