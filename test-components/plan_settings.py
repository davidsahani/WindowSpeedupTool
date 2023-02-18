import os
import sys

from PyQt6.QtWidgets import QApplication, QFrame, QStackedWidget

# append parent dir to python import path
parent_dir: str = os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir))
sys.path.append(parent_dir)
# switch to parent dir
os.chdir(parent_dir)

# prevent automatic pep8 import organization
from poweroptions.plan_settings import PlanSettings  # nopep8
from utils import power  # nopep8


class Window(PlanSettings):
    def removeSelf(self) -> None:
        pass


def main() -> None:
    import qdarkstyle  # type: ignore
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(  # type: ignore
        qt_api='pyqt6'))

    name, guid = power.active()
    stacked_widget = QStackedWidget()
    master = QFrame(stacked_widget)
    widget = Window(master, stacked_widget, name, guid)
    stacked_widget.addWidget(widget)
    stacked_widget.setCurrentWidget(widget)
    stacked_widget.setWindowTitle("Plan Settings")
    stacked_widget.resize(650, 450)
    stacked_widget.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
