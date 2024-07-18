from enum import IntEnum
from functools import partial

from PyQt6.QtCore import pyqtSignal, QMutex, QMutexLocker
from PyQt6.QtWidgets import QFrame, QStackedWidget, QVBoxLayout, QWidget

from utils import styles
from utils.threads import Thread

from .clean import clean_eventlogs, clean_junkfiles, clean_windows_updates
from .cleaner_gui import CleanerGui
from .cleanup_view import CleanupView


class CleanupTask(IntEnum):
    ALL_CHECKED = 0
    JUNK_CLEANUP = 1
    EVENT_LOGS = 2
    WINDOWS_UPDATE = 3


class SystemCleaner(QFrame):
    signal = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setupWidgets()
        self.connectSlots()
        self.setStyleSheet(styles.get("cleaner"))

        self.__mutex = QMutex()
        self.__cancel_flag = False
        self.threads: dict[CleanupTask, Thread] = {}
        self.thread_states: dict[CleanupTask, bool] = {}

    def setupWidgets(self) -> None:
        """Setup the widgets in layout."""
        self.cleaner_gui = CleanerGui()
        self.cleanup_view = CleanupView()

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.cleaner_gui)
        self.stacked_widget.addWidget(self.cleanup_view)

        layout = QVBoxLayout()
        layout.addWidget(self.stacked_widget)
        self.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def connectSlots(self) -> None:
        """Connect the callbacks to their corresponding events."""
        self.cleaner_gui.circle_button.clicked.connect(
            partial(self.runCleanup, CleanupTask.ALL_CHECKED)
        )
        self.cleaner_gui.clean_button.clicked.connect(
            partial(self.runCleanup, CleanupTask.JUNK_CLEANUP)
        )
        self.cleaner_gui.clean_event_logs_button.clicked.connect(
            partial(self.runCleanup, CleanupTask.EVENT_LOGS)
        )
        self.cleaner_gui.clean_windows_update_button.clicked.connect(
            partial(self.runCleanup, CleanupTask.WINDOWS_UPDATE)
        )
        self.cleanup_view.connectClose(lambda: (
            self.stacked_widget.setCurrentWidget(self.cleaner_gui),
            self.thread_states.clear(),  # clear previous thread states.
            self.cleanup_view.text_widget.clear()  # clear previous messages.
        ))
        self.cleanup_view.connectCancel(lambda: (
            self.cancel(), self.cleanup_view.
            setBorderMessage("Canceled cleanup operation")
        ))
        self.signal.connect(self.cleanup_view.appendText)

    def runCleanup(self, task: CleanupTask) -> None:
        """Run cleanup task in a new thread."""
        self.reset_cancel()

        if task != CleanupTask.ALL_CHECKED:
            thread = self.threads.get(task)
            if thread is None:
                match task:
                    case CleanupTask.JUNK_CLEANUP:
                        thread = Thread(self.cleanJunkFiles)
                    case CleanupTask.EVENT_LOGS:
                        thread = Thread(self.cleanEventLogs)
                    case CleanupTask.WINDOWS_UPDATE:
                        thread = Thread(self.cleanWindowsUpdates)

                self.threads[task] = thread
                thread.started.connect(partial(self.onThreadStarted, task))
                thread.finished.connect(partial(self.onThreadFinished, task))

            thread.start()
        else:
            thread = self.threads.get(CleanupTask.JUNK_CLEANUP)  # noqa
            if thread is None:
                thread = Thread(self.cleanJunkFiles)
                thread.started.connect(
                    partial(self.onThreadStarted, CleanupTask.JUNK_CLEANUP))
                thread.finished.connect(
                    partial(self.onThreadFinished, CleanupTask.JUNK_CLEANUP))
                self.threads[CleanupTask.JUNK_CLEANUP] = thread

            thread.start()

            if self.cleaner_gui.clean_event_logs_checkbox.isChecked():
                thread = self.threads.get(CleanupTask.EVENT_LOGS)  # noqa
                if thread is None:
                    thread = Thread(self.cleanEventLogs)
                    thread.started.connect(
                        partial(self.onThreadStarted, CleanupTask.EVENT_LOGS))
                    thread.finished.connect(
                        partial(self.onThreadFinished, CleanupTask.EVENT_LOGS))
                    self.threads[CleanupTask.EVENT_LOGS] = thread

                thread.start()

            if self.cleaner_gui.clean_windows_update_checkbox.isChecked():
                thread = self.threads.get(CleanupTask.WINDOWS_UPDATE)  # noqa
                if thread is None:
                    thread = Thread(self.cleanWindowsUpdates)
                    thread.started.connect(
                        partial(self.onThreadStarted, CleanupTask.WINDOWS_UPDATE))
                    thread.finished.connect(
                        partial(self.onThreadFinished, CleanupTask.WINDOWS_UPDATE))
                    self.threads[CleanupTask.WINDOWS_UPDATE] = thread

                thread.start()

        if self.stacked_widget.currentWidget() is not self.cleanup_view:
            self.stacked_widget.setCurrentWidget(self.cleanup_view)
        self.cleanup_view.border_widget.showCloseButton(False)

    def onThreadStarted(self, task: CleanupTask) -> None:
        """Handle cleanup task thread started."""
        self.thread_states[task] = False  # implies running

        messages: list[str] = []
        for task in self.threads:
            state = self.thread_states.get(task)
            if state is None or state:
                continue  # finished or not started

            match task:
                case CleanupTask.JUNK_CLEANUP:
                    msg = "junk files"
                case CleanupTask.EVENT_LOGS:
                    msg = "event logs"
                case CleanupTask.WINDOWS_UPDATE:
                    msg = "windows updates files"
                case CleanupTask.ALL_CHECKED:
                    msg = ""
            messages.append(msg)

        message = f"Cleaning up {', '.join(messages)}..."
        self.cleanup_view.setBorderMessage(message)

    def onThreadFinished(self, task: CleanupTask) -> None:
        """Handle cleanup task thread finished."""
        self.thread_states[task] = True  # implies finished

        messages: list[str] = []
        for task in self.threads:
            state = self.thread_states.get(task)
            if state is None or not state:
                continue  # running or not started

            match task:
                case CleanupTask.JUNK_CLEANUP:
                    msg = "junk files"
                case CleanupTask.EVENT_LOGS:
                    msg = "event logs"
                case CleanupTask.WINDOWS_UPDATE:
                    msg = "windows updates files"
                case CleanupTask.ALL_CHECKED:
                    msg = ""
            messages.append(msg)

        message = f"Finished Cleaning up {', '.join(messages)}."
        self.cleanup_view.setBorderMessage(message)

        if all(self.thread_states.values()):
            self.cleanup_view.border_widget.showCloseButton(True)

    def cancel(self) -> None:
        with QMutexLocker(self.__mutex):
            self.__cancel_flag = True

    def reset_cancel(self) -> None:
        with QMutexLocker(self.__mutex):
            self.__cancel_flag = False

    def is_cancelled(self) -> bool:
        with QMutexLocker(self.__mutex):
            return self.__cancel_flag

    def cleanJunkFiles(self) -> None:
        """Clean system junk files."""
        for msg in clean_junkfiles():
            if self.is_cancelled():
                break
            self.signal.emit(msg)

    def cleanEventLogs(self) -> None:
        """Clean system event logs."""
        for msg in clean_eventlogs():
            if self.is_cancelled():
                break
            self.signal.emit(msg)

    def cleanWindowsUpdates(self) -> None:
        """Clean windows updates."""
        for msg in clean_windows_updates():
            if self.is_cancelled():
                break
            self.signal.emit(msg)
