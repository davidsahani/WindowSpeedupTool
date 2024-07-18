import sys

import _set_source_path  # noqa
from PyQt6.QtWidgets import QApplication, QStackedWidget
import qdarkstyle  # type: ignore

from source.drivers_backup import DriversBackup
from source.utils.threads import CommandThread


class DriversBackupTest(DriversBackup):
    def startUninstall(self, row: int) -> None:
        """Overwritten:
            can't have drivers accidentally
            uninstalled during testing
        """
        if self.uninstall_thread and self.uninstall_thread.isRunning():
            self.showUninstallRunningWarning()
            return

        published_name = self.drivers_view.publishedName(row)
        self.uninstall_thread = CommandThread(["timeout", "3"])
        self.uninstall_thread.connect(
            lambda result: self.onUninstallFinish(result, row)
        )
        if not (self.backup_thread and self.backup_thread.isRunning()):
            self.border_widget.displayMessage(
                f"Uninstalling Driver: {published_name}"
            )
        self.uninstall_thread.start()


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(  # type: ignore
        qt_api='pyqt6'))

    stacked_Widget = QStackedWidget()
    widget = DriversBackupTest(stacked_Widget)
    stacked_Widget.addWidget(widget)
    stacked_Widget.setWindowTitle("Drivers Backup")
    stacked_Widget.resize(750, 550)
    stacked_Widget.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
