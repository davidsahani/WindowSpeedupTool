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
import styles  # nopep8
from poweroptions.power_throttling import PowerThrottling  # nopep8


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(  # type: ignore
        qt_api='pyqt6'))

    widget = PowerThrottling()
    widget.setWindowTitle("Power Throttling Window")
    widget.setStyleSheet(styles.get("power"))
    widget.resize(750, 550)
    widget.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
