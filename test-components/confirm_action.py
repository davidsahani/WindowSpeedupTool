import os
import sys

from PyQt6.QtWidgets import QApplication, QStackedWidget, QWidget

from utils import service

# append parent dir to python import path
parent_dir: str = os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir))
sys.path.append(parent_dir)

# prevent automatic pep8 import organization
from windowservices.confirm_action import ConfirmServiceAction  # nopep8


def main() -> None:
    import qdarkstyle  # type: ignore
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(  # type: ignore
        qt_api='pyqt6'))

    master_Widget = QWidget()
    stacked_widget = QStackedWidget()
    running_services = [service_name for service_name, *_ in service.running()]
    services = {service_name: service.info(
        service_name)['start_type'] for service_name, in running_services}

    widget = ConfirmServiceAction(master_Widget, stacked_widget, services)
    widget.displayMessage("Do you want to make these changes | Test")
    stacked_widget.addWidget(widget)
    stacked_widget.setWindowTitle("Confirm service action")
    stacked_widget.resize(650, 450)
    stacked_widget.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
