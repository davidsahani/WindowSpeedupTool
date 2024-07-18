import sys

import _set_source_path  # noqa
from PyQt6.QtWidgets import QApplication
import qdarkstyle  # type: ignore

from source.widgets.stacked_widget import StackedWidget
from source.window_services import WindowServices


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(  # type: ignore
        qt_api='pyqt6'))
    main_widget = StackedWidget()
    widget = WindowServices(main_widget)
    main_widget.addWidget(widget)
    main_widget.setWindowTitle("Windows Services")
    main_widget.resize(788, 560)
    main_widget.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
