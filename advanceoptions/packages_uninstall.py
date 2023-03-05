from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QFrame, QMessageBox, QStackedWidget, QVBoxLayout,
                             QWidget)

import styles
from widgets.process_terminal import ProcessTerminal
from widgets.sizegrip import SizeGrip

from .loading_widget import LoadingWidget
from .packages_view import PackagesView


class Terminal(ProcessTerminal):
    def showWarning(self) -> None:
        QMessageBox.warning(
            self, "Can't run another uninstall",
            "Already uninstalling package.",
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Ok
        )


class PackagesUninstall(QFrame):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self._parent = parent
        self.setupWidgets()
        self.setStyleSheet(styles.get("drivers"))

    def setupWidgets(self) -> None:
        """Setup the widgets in layout"""
        self.stacked_widget = QStackedWidget(self)
        self.loading_widget = LoadingWidget(self.stacked_widget)

        self.main_widget = QWidget(self.stacked_widget)
        self.packages_view = PackagesView(self.main_widget)
        self.packages_view.connectFinish(self.setMainWidget)
        self.packages_view.connectUninstall(self.startUninstall)

        self.terminal = Terminal(self)
        size_grip = SizeGrip(self, self.terminal)
        size_grip.hide()      # hide initially
        self.terminal.hide()  # hide initially

        vlayout = QVBoxLayout(self.main_widget)
        vlayout.addWidget(self.packages_view)
        vlayout.addWidget(size_grip)
        vlayout.addWidget(self.terminal)
        vlayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        vlayout.setContentsMargins(0, 0, 0, 0)
        self.main_widget.setLayout(vlayout)

        self.stacked_widget.addWidget(self.loading_widget)
        self.stacked_widget.addWidget(self.main_widget)

        layout = QVBoxLayout(self)
        layout.addWidget(self.stacked_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def setMainWidget(self) -> None:
        """Set main driver widget"""
        self.stacked_widget.setCurrentWidget(self.main_widget)
        self.stacked_widget.removeWidget(self.loading_widget)
        self.loading_widget.deleteLater()

    def startUninstall(self, row: int) -> None:
        """Start package uninstall in new thread"""
        package_id = self.packages_view.packages[row][0]
        cmd = f"dism /online /Remove-Package /PackageName:{package_id}"
        self.terminal.runCommand(cmd)
        self.terminal.connectFinish(
            lambda s: self.onUninstallFinish(s, row))

    def onUninstallFinish(self, status: int, row: int) -> None:
        """Remove the selected row"""
        if status:
            return  # on failure
        self.packages_view.model().removeRow(row)
