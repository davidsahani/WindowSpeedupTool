import sys

import _set_source_path  # noqa
from PyQt6.QtWidgets import QApplication
import qdarkstyle  # type: ignore

from source.utils import service
from source.utils.config_parser import Service
from source.widgets.stacked_widget import StackedWidget
from source.window_services.confirm_widget import ConfirmActionWidget


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(  # type: ignore
        qt_api='pyqt6'))

    running_services = [service_name for service_name, *_ in service.running()]

    services: list[Service] = []

    for service_name in running_services:
        info = service.info(service_name).value
        if info is None:
            continue
        services.append(Service(
            service_name=service_name,
            display_name=info['display_name'],
            startup_type=info['start_type']
        ))

    stacked_widget = StackedWidget()

    widget = ConfirmActionWidget(
        stacked_widget, services, True
    )
    stacked_widget.addWidget(widget)

    widget.displayPrompt("Confirm Services Action | TEST")
    widget.message_bar.connect(stacked_widget.close)
    widget.message_bar.connectCancel(stacked_widget.close)

    stacked_widget.setWindowTitle("Confirm Services Action")
    stacked_widget.resize(788, 560)
    stacked_widget.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
