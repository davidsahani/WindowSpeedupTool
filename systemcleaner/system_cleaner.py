from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QCheckBox, QFrame, QGridLayout, QPushButton,
                             QSizePolicy, QSpacerItem, QStackedWidget,
                             QVBoxLayout, QWidget)

import styles
from widgets.process_terminal import Thread

from .clean import clean_eventlogs, clean_junkfiles, clean_windows_updates
from .cleanup_view import CleanupView


class CleanerGui(QWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setupWidgets()

    def setupWidgets(self) -> None:
        """Setup widgets in layout"""
        self.circle_button = QPushButton()
        self.circle_button.setObjectName("CircleButton")

        self.clean_button = QPushButton("Clean Junk Files")
        self.clean_button.setObjectName("CleanButton")

        spacer = QSpacerItem(  # spacer item for extra spacing
            20, 10, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        spacer1 = QSpacerItem(  # spacer item for extra spacing
            20, 10, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout()
        layout.addWidget(self.circle_button)
        layout.addSpacerItem(spacer)
        layout.addWidget(self.clean_button)
        layout.addSpacerItem(spacer1)
        layout.addWidget(self.makeWidget())
        self.setLayout(layout)

    def makeWidget(self) -> QWidget:
        """Make bottom widget containing checkboxes and buttons"""
        self.clean_event_logs_checkbox = QCheckBox()
        self.clean_windows_update_checkbox = QCheckBox()
        self.clean_event_logs_checkbox.setChecked(True)

        self.clean_event_logs_button = QPushButton("Clean Event Logs")
        self.clean_windows_update_button = QPushButton("Clean Windows Updates")

        widget = QWidget(self)
        layout = QGridLayout(widget)
        layout.addWidget(self.clean_event_logs_checkbox, 0, 0)
        layout.addWidget(self.clean_event_logs_button, 0, 1)
        layout.addWidget(self.clean_windows_update_checkbox, 1, 0)
        layout.addWidget(self.clean_windows_update_button, 1, 1)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeading)
        layout.setHorizontalSpacing(0)
        layout.setVerticalSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)
        return widget


# *================================================
# *              SYSTEM CLEANER                   *
# *================================================


class SystemCleaner(QFrame):
    signal = pyqtSignal(str)
    signal1 = pyqtSignal(str)
    signal2 = pyqtSignal(str)

    def __init__(self, parent: QStackedWidget) -> None:
        super().__init__(parent)
        self._parent = parent
        self.setupWidgets()
        self.connectSlots()
        self.setStyleSheet(styles.get("cleaner"))
        self.cleanup_view: CleanupView = None  # type: ignore
        self.__cleanup_thread: Thread | None = None
        self.__event_cleanup_thread: Thread | None = None
        self.__update_cleanup_thread: Thread | None = None

    def setupWidgets(self) -> None:
        """Setup widgets in layout."""
        self.cleaner_gui = CleanerGui(self)

        layout = QVBoxLayout()
        layout.addWidget(self.cleaner_gui)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def connectSlots(self) -> None:
        """Connect events to their corresponding methods"""
        self.cleaner_gui.circle_button.\
            clicked.connect(lambda: self.openCleanupView() or  # type: ignore
                            self.runCleanup())
        self.cleaner_gui.clean_button.\
            clicked.connect(lambda: self.openCleanupView() or  # type: ignore
                            self.runCleanup())
        self.cleaner_gui.clean_event_logs_button.\
            clicked.connect(lambda: self.openCleanupView() or  # type: ignore
                            self.runEventLogsCleanup())
        self.cleaner_gui.clean_windows_update_button.\
            clicked.connect(lambda: self.openCleanupView() or  # type: ignore
                            self.runWindowsUpdateCleanup())

    def openCleanupView(self) -> None:
        """Open Cleanup View widget"""
        self.cleanup_view = CleanupView(self, self._parent)
        self.cleanup_view.setStyleSheet(self.styleSheet())
        self.cleanup_view.connectCancel(self.onCancel)

    def onCancel(self) -> None:
        """Kill the threads on Cleanup View cancel press"""
        if self.__cleanup_thread and self.__cleanup_thread.isRunning():
            self.__cleanup_thread.terminate()
        if self.__event_cleanup_thread and self.__event_cleanup_thread.isRunning():
            self.__event_cleanup_thread.terminate()
        if self.__update_cleanup_thread and self.__update_cleanup_thread.isRunning():
            self.__update_cleanup_thread.terminate()
        self.cleanup_view.setMessage("Canceled cleanup operation")

    def appendText(self, text: str) -> None:
        """Append text to cleanup view's text widget"""
        self.cleanup_view.appendText(text)

    def runCleanup(self) -> None:
        """Run windows junk cleanup in new thread"""
        self.__cleanup_thread = Thread(self.cleanJunkFiles)
        self.__cleanup_thread.start()

        self.signal.connect(self.appendText)
        self.__cleanup_thread.finished.connect(  # type: ignore
            lambda: self.signal.disconnect(self.appendText))

        self.cleanup_view.setText("Cleaning up junk files")
        self.__cleanup_thread.finished.connect(  # type: ignore
            lambda: self.cleanup_view.setMessage(
                "Finished cleaning up junk files")
        )
        if self.cleaner_gui.clean_event_logs_checkbox.isChecked():
            self.runEventLogsCleanup()
        if self.cleaner_gui.clean_windows_update_checkbox.isChecked():
            self.runWindowsUpdateCleanup()

    def runEventLogsCleanup(self) -> None:
        """Run windows event log cleanup in new thread"""
        self.__event_cleanup_thread = Thread(self.cleanEventLogs)
        self.__event_cleanup_thread.start()

        self.signal1.connect(self.appendText)
        self.__event_cleanup_thread.finished.connect(  # type: ignore
            lambda: self.signal1.disconnect(self.appendText))

        if self.__cleanup_thread and self.__cleanup_thread.isRunning():
            return  # cleanup thread is already running
        self.cleanup_view.setText("Cleaning up event logs")
        self.__event_cleanup_thread.finished.connect(  # type: ignore
            lambda: self.cleanup_view.setMessage(
                "Finished cleaning up event logs")
        )

    def runWindowsUpdateCleanup(self) -> None:
        """Run windows update cleanup in new thread"""
        self.__update_cleanup_thread = Thread(self.cleanWindowsUpdates)
        self.__update_cleanup_thread.start()

        self.signal2.connect(self.appendText)
        self.__update_cleanup_thread.finished.connect(  # type: ignore
            lambda: self.signal2.disconnect(self.appendText))

        if self.__cleanup_thread and self.__cleanup_thread.isRunning():
            return  # cleanup thread is already running
        self.cleanup_view.setText("Cleaning up windows updates files")
        self.__update_cleanup_thread.finished.connect(  # type: ignore
            lambda: self.cleanup_view.setMessage(
                "Finished cleaning windows updates files")
        )

    def cleanJunkFiles(self) -> None:
        """Clean system junk files"""
        for msg in clean_junkfiles():
            self.signal.emit(msg)

    def cleanEventLogs(self) -> None:
        """Clean event logs"""
        for msg in clean_eventlogs():
            self.signal1.emit(msg)

    def cleanWindowsUpdates(self) -> None:
        """Clean windows updates"""
        for msg in clean_windows_updates():
            self.signal2.emit(msg)
