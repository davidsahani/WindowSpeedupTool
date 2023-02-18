import os
import sys

from PyQt6.QtWidgets import QApplication, QStackedWidget, QWidget

# append parent dir to python import path
parent_dir: str = os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir))
sys.path.append(parent_dir)
# switch to parent dir
os.chdir(parent_dir)

# prevent automatic pep8 import organization
from utils.config import NORMAL_SERVICES, NORMAL_SPECIFIC  # nopep8
from windowservices.normal_specific_services import \
    NormalSpecificServices  # nopep8


def main() -> None:
    import qdarkstyle  # type: ignore
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(  # type: ignore
        qt_api='pyqt6'))

    stacked_widget = QStackedWidget()
    master_widget = QWidget(stacked_widget)
    widget = NormalSpecificServices(
        master_widget, stacked_widget, NORMAL_SPECIFIC, NORMAL_SERVICES)
    stacked_widget.setWindowTitle("Normal Specific Services")
    stacked_widget.resize(750, 550)
    stacked_widget.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
