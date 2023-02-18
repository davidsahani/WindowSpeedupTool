import os
import sys

import qdarkstyle  # type: ignore
from PyQt6.QtWidgets import QApplication

# append parent dir to python import path
parent_dir: str = os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir))
sys.path.append(parent_dir)
# switch to parent dir
os.chdir(parent_dir)

# prevent automatic pep8 import organization
from systemrepair import SystemRepair  # nopep8


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(  # type: ignore
        qt_api='pyqt6'))
    widget = SystemRepair()
    widget.setWindowTitle("System Repair")
    widget.resize(650, 450)
    widget.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
