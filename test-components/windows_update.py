import os
import sys

import qdarkstyle  # type: ignore
from PyQt6.QtWidgets import QApplication, QStackedWidget

# append parent dir to python import path
parent_dir: str = os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir))
sys.path.append(parent_dir)
# switch to parent dir
os.chdir(parent_dir)

# prevent automatic pep8 import organization
from windowsupdate import WindowsUpdate  # nopep8


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(  # type: ignore
        qt_api='pyqt6'))
    main_widget = QStackedWidget()
    widget = WindowsUpdate(main_widget)
    main_widget.addWidget(widget)
    main_widget.setWindowTitle("System Cleaner")
    main_widget.resize(650, 450)
    main_widget.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
