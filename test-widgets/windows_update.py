import sys

import _set_source_path  # noqa
from PyQt6.QtWidgets import QApplication, QStackedWidget
import qdarkstyle  # type: ignore

from source.windows_update import WindowsUpdate


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(  # type: ignore
        qt_api='pyqt6'))
    main_widget = QStackedWidget()
    widget = WindowsUpdate(main_widget)
    main_widget.addWidget(widget)
    main_widget.setWindowTitle("Windows Update")
    main_widget.resize(650, 450)
    main_widget.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
