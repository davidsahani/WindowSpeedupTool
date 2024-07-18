from typing import override, Sequence

from PyQt6.QtCore import QEvent, QPoint, Qt
from PyQt6.QtGui import QFontMetrics, QPainter
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QGroupBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from utils import styles

from . import sysinfo


class LineSpacingLabel(QLabel):
    @override
    def paintEvent(self, a0: QEvent | None) -> None:
        painter = QPainter(self)
        metrics = QFontMetrics(self.font())
        line_height = metrics.height() * 1.5  # adjust the line spacing here
        y = 0
        for line in self.text().splitlines():
            painter.drawText(QPoint(0, int(y) + metrics.ascent()), line)
            y += line_height
        painter.end()
        # adjust widget size respect to line spacing.
        height = y + metrics.descent() - 6.5
        self.setFixedHeight(int(height))


class SystemInfo(QFrame):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setupWidgets()
        self.setStyleSheet(styles.get("sysinfo"))

    def setupWidgets(self) -> None:
        """Setup the widgets in layout."""
        layout = QVBoxLayout()

        widgets_data = [
            ("Processor", self.formatText(sysinfo.processor())),
            ("Gpu", self.formatTextList(sysinfo.gpus())),
            ("Ram", self.formatTextList(sysinfo.rams())),
            ("Disk", self.formatTextList(sysinfo.disks())),
            ("Motherboard", self.formatText(sysinfo.motherboard())),
            ("Network Adapter", self.formatTextList(sysinfo.net_adapters())),
            ("Operating System", self.formatText(sysinfo.os_info()))
        ]

        for title, data in widgets_data:
            group_box = self.createGroupTextWidget(data)
            group_box.setTitle(title)
            layout.addWidget(group_box)

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

    @staticmethod
    def formatText(values: Sequence[tuple[str, str | int | bool]]) -> str:
        """Format text for the group widget."""
        return '\n'.join((f"{name}: {value}" for name, value in values))

    @staticmethod
    def formatTextList(values_list: Sequence[Sequence[tuple[str, str | int]]]) -> str:
        """Format text list for the group widget."""
        result: list[str] = []
        for values in values_list:
            result.append(
                '\n'.join((f"{name}: {value}" for name, value in values))
            )
            result.append('\n\n')
        if result:
            result.pop()  # remove last '\n'.
        return ''.join(result)

    def createGroupTextWidget(self, text: str) -> QGroupBox:
        """Create GroupBox widget with specified text."""
        label = LineSpacingLabel(text)

        copy_button = QPushButton()
        copy_button.setToolTip("copy")
        copy_button.setObjectName("CopyButton")
        copy_button.clicked.connect(
            lambda: self.copyTextToClipboard(text)
        )

        layout = QGridLayout()
        layout.addWidget(label, 0, 0)
        layout.addWidget(copy_button, 0, 1, Qt.AlignmentFlag.AlignTop
                         | Qt.AlignmentFlag.AlignRight)
        gbox = QGroupBox()
        gbox.setLayout(layout)
        return gbox

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
