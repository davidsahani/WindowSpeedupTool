import sys

import _set_source_path  # noqa
from PyQt6.QtWidgets import QApplication
import qdarkstyle  # type: ignore

from source.system_repair import SystemRepair


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
