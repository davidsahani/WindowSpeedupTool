import sys

import _set_source_path  # noqa
from PyQt6.QtWidgets import QApplication
import qdarkstyle  # type: ignore

from source.power_options.plan_settings import PlanSettings
from source.utils import power
from source.widgets.stacked_widget import StackedWidget


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(  # type: ignore
        qt_api='pyqt6'))

    result = power.active()
    if result.value is None:
        print(result.error, file=sys.stderr)

    name, guid = result.value or ('Not Retrieved', '')

    stacked_widget = StackedWidget()
    widget = PlanSettings(stacked_widget, name, guid)
    stacked_widget.addWidget(widget)
    stacked_widget.setCurrentWidget(widget)
    stacked_widget.setWindowTitle("Plan Settings")
    stacked_widget.resize(650, 450)
    stacked_widget.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
