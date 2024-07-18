import sys

import _set_source_path  # noqa
from PyQt6.QtWidgets import QApplication
import qdarkstyle  # type: ignore

from source.power_options import PowerOptions
from source.widgets.stacked_widget import StackedWidget


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(  # type: ignore
        qt_api='pyqt6'))
    main_widget = StackedWidget()
    widget = PowerOptions(main_widget)
    main_widget.addWidget(widget)
    main_widget.setWindowTitle("Power Options")
    main_widget.resize(650, 480)
    main_widget.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
