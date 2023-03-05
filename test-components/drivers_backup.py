import os
import sys
from typing import Generator

import qdarkstyle  # type: ignore
from PyQt6.QtWidgets import QApplication, QStackedWidget

# append parent dir to python import path
parent_dir: str = os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir))
sys.path.append(parent_dir)
# switch to parent dir
os.chdir(parent_dir)

# prevent automatic pep8 import organization
from driversbackup import DriversBackup  # nopep8


def load_drives_from_file() -> Generator[list[str], None, None]:
    "Yield all available drivers from file."

    # Dism /online /get-drivers /format:table > drivers_list.txt

    with open('drivers_list.txt') as file:
        output = file.read()

    for line in output.splitlines():
        values = line.split('|')
        if not values[0].strip().endswith('.inf'):
            continue
        yield [v.strip() for v in values]


class TestWidget(DriversBackup):
    def uninstallDriver(self, row: int) -> None:
        """Overwritten:
            can't have drivers accidentally
            uninstalled during testing
        """

        # self.signal1.emit(0, row)   # `0` for success
        self.signal1.emit(1, row)   # `1` for failure


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(  # type: ignore
        qt_api='pyqt6'))

    stacked_Widget = QStackedWidget()
    widget = TestWidget(stacked_Widget)
    stacked_Widget.addWidget(widget)
    stacked_Widget.setWindowTitle("Drivers Manager")
    stacked_Widget.resize(750, 550)
    stacked_Widget.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
