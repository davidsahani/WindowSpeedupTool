import subprocess
from typing import Callable, override

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QCloseEvent, QTextCursor
from PyQt6.QtWidgets import QDockWidget, QMessageBox, QPlainTextEdit, QWidget

from utils.threads import PROCESS_STARTUP_INFO, Thread


class ProcessTerminal(QDockWidget):
    _signal = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setupWidgets()
        self.__thread = None
        self.__function = None
        self.__return_code = -1
        self._signal.connect(self.insertText)

    def setupWidgets(self) -> None:
        """Set the text widget in QDockWidget."""
        self.text_widget = QPlainTextEdit(self)
        self.setWidget(self.text_widget)
        self.text_widget.setReadOnly(True)

    def runCommand(self, command: list[str]) -> None:
        """Run the specified command in new thread."""
        if self.__thread and self.__thread.isRunning():
            self.showWarning()
            return
        self.clearText()  # clear output of previous process.
        title_text = f"Running: {' '.join(command)}"
        self.setWindowTitle(title_text)
        self.__thread = Thread(self._executeCommand, command)
        self.__thread.finished.connect(
            lambda: self.setWindowTitle(f"Finished {title_text}")
        )
        self.__thread.finished.connect(
            lambda: self.__function(self.__return_code) if
            self.__function is not None else None
        )
        self.__thread.start()
        self.show()  # show the dock widget, it could be hidden.

    def _executeCommand(self, command: list[str]) -> None:
        """Execute the command in a new process and emit its output."""
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=PROCESS_STARTUP_INFO,
        )
        self.process = process
        stdout_stream = process.stdout

        if stdout_stream is not None:
            while True:
                output = stdout_stream.readline()
                if output == b'' and process.poll() is not None:
                    break  # process ended
                if not output:
                    continue  # empty strings

                self._signal.emit(output.decode())  # update text widget

        self.__return_code = process.wait()  # save process return code.

    def insertText(self, text: str) -> None:
        """Insert text into text-widget and update cursor position."""
        self.text_widget.insertPlainText(text)
        # move the cursor to the end of the line.
        cursor = self.text_widget.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
        self.text_widget.setTextCursor(cursor)

    def clearText(self) -> None:
        """Clear text-widget text."""
        self.text_widget.setReadOnly(False)
        self.text_widget.clear()
        self.text_widget.setReadOnly(True)

    def showWarning(self) -> None:
        """Show process running warning."""
        QMessageBox.warning(
            self, "Can't run command",
            "Previous command is still running.",
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Ok
        )

    @override
    def closeEvent(self, event: QCloseEvent | None) -> None:
        """Kill the process on close button press."""
        self.process.kill()
        self.clearText()
        super().closeEvent(event)

    def connectFinish(self, function: Callable[[int], None]) -> None:
        """Connect the function to process thread finish event.

        Receive:
            process returncode
        """
        self.__function = function
