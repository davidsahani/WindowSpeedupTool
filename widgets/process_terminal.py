import subprocess
from typing import Any, Callable

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QCloseEvent, QTextCursor
from PyQt6.QtWidgets import QDockWidget, QMessageBox, QPlainTextEdit, QWidget

from utils.power import PROCESS_STARTUP_INFO


class Thread(QThread):
    def __init__(self, function: Callable[..., Any], *args: Any) -> None:
        super().__init__()
        self.__function = function
        self.__args = args

    def run(self) -> None:
        self.__function(*self.__args)


class ProcessTerminal(QDockWidget):
    signal = pyqtSignal(str)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setupWidgets()
        self.__thread = None
        self.__function = None

    def setupWidgets(self) -> None:
        """set the text widget in QDockWidget"""
        self.text_widget = QPlainTextEdit(self)
        self.setWidget(self.text_widget)
        self.text_widget.setReadOnly(True)

    def showWarning(self) -> None:
        """Show process running warning"""
        QMessageBox.warning(
            self, "Can't run command",
            "Previous command is still running.",
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Ok
        )

    def runCommand(self, command: str) -> None:
        """Run the given command in new thread"""
        if self.__thread and self.__thread.isRunning():
            self.showWarning()
            return
        self.clearText()  # clear output of previous process

        self.setWindowTitle(f"Running: {command}")
        self.__thread = Thread(self._startProcess, command)
        self.__thread.start()
        self.signal.connect(self.insertText)
        self.__thread.finished.connect(  # type: ignore
            lambda: self.setWindowTitle(f"Finished Running: {command}") or
            # reset signal handler for previous process
            self.signal.disconnect(self.insertText)
        )
        if self.isHidden():
            self.show()

    def _startProcess(self, command: str) -> None:
        """Start the command in process and update text widget"""
        proc = subprocess.Popen(
            command, stdout=subprocess.PIPE,
            startupinfo=PROCESS_STARTUP_INFO
        )
        self.process = proc

        while True:
            output = proc.stdout.readline()  # type: ignore
            if output == b'' and proc.poll() is not None:
                break
            if not output:
                continue  # if empty strings
            self.signal.emit(output.decode())  # update text widget

        if self.__function is not None:
            self.__function(proc.wait())

    def insertText(self, text: str) -> None:
        """Insert text into text-widget and update cursor position"""
        self.text_widget.insertPlainText(text)
        # move the cursor to the end of the line
        cursor = self.text_widget.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
        self.text_widget.setTextCursor(cursor)

    def clearText(self) -> None:
        """Clear text-widget text"""
        self.text_widget.setReadOnly(False)
        self.text_widget.clear()
        self.text_widget.setReadOnly(True)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Kill the process on close button press"""
        self.process.kill()
        self.clearText()
        super().closeEvent(event)

    def connectFinish(self, function: Callable[[int], None]) -> None:
        """Connect the function to process thread finish event.

        Receive:
            returncode of process
        """
        self.__function = function
