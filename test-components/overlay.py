import os
import sys
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QGridLayout, QWidget

# append parent dir to python import path
parent_dir: str = os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir))
sys.path.append(parent_dir)

# prevent automatic pep8 import organization
from widgets.overlay import MessageOverlay  # nopep8


class MainWindow(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.makeWidgets()

    def makeWidgets(self) -> None:
        text = "Message Overlay"
        overlay = MessageOverlay(self)
        overlay.displayMessage(text, True)

        layout = QGridLayout(self)
        layout.addWidget(overlay)
        layout.setAlignment(Qt.AlignmentFlag.AlignBottom)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)


if __name__ == '__main__':
    import qdarkstyle  # type: ignore
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(  # type: ignore
        qt_api='pyqt6'))
    main = MainWindow()
    main.resize(650, 450)
    main.setWindowTitle("Message overlay window")
    main.show()
    sys.exit(app.exec())
