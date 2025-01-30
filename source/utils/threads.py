import subprocess
from typing import Any, Callable, Concatenate, override, ParamSpec, TypeVar

from PyQt6.QtCore import pyqtSignal, QObject, QThread

P = ParamSpec('P')
R = TypeVar('R')

# To hide process console window
PROCESS_STARTUP_INFO = subprocess.STARTUPINFO()
PROCESS_STARTUP_INFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW


class Error(Exception):
    def __init__(self, winerr: int, stderr: str, /) -> None:
        self.winerr = winerr
        self.stderr = stderr
        super().__init__(winerr, stderr)


class StatusResult:
    def __init__(self, status: int, error: str = "") -> None:
        self.status = status
        self.error = error

    @property
    def success(self) -> bool:
        return self.status == 0

    @override
    def __repr__(self) -> str:
        return f"{self.status, self.error}"


class Result[T]:
    def __init__(
        self, value: T | None = None,
        error: Error = Error(0, "")
    ) -> None:
        self.value = value
        self.error = error

    @override
    def __repr__(self) -> str:
        return repr(self.value)

    def status(self) -> StatusResult:
        return StatusResult(self.error.winerr, self.error.stderr)

    @staticmethod
    def from_command(command: list[str]) -> 'Result[str]':
        return Result.from_process(
            subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=PROCESS_STARTUP_INFO
            )
        )

    @staticmethod
    def from_process(process: subprocess.Popen[bytes]) -> 'Result[str]':
        stdout, stderr = process.communicate()
        output = (stdout or b'').decode().strip()
        error = (stderr or b'').decode().strip()

        status = process.wait()
        if status == 0:
            return Result(output)

        if not error and output:
            error = output  # error may be at stdout
        command = " ".join(process.args)  # type: ignore
        if error:
            error = f"ProcessError: {command}\n\n{error}"
        else:
            error = f"{command}, Failed with status code: {status}"
        return Result(error=Error(status, error))


class Thread(QThread):
    def __init__(self, func: Callable[Concatenate[P], R], *args: P.args, **kwargs: P.kwargs) -> None:
        super().__init__()
        self.__func_args = func, args, kwargs

    @override
    def run(self) -> None:
        func, args, kwargs = self.__func_args
        func(*args, **kwargs)


class ProcessThread(QThread):
    _finished = pyqtSignal(Result)

    def __init__(self, process: subprocess.Popen[bytes], parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.process = process

    @override
    def run(self) -> None:
        self._finished.emit(Result.from_process(self.process))

    def connect(self, function: Callable[[Result[str]], Any]) -> None:
        self._finished.connect(function)


class CommandThread(QThread):
    _finished = pyqtSignal(Result)

    def __init__(self, command: list[str], parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.command = command

    @override
    def run(self) -> None:
        self._finished.emit(Result.from_command(self.command))

    def connect(self, function: Callable[[Result[str]], Any]) -> None:
        self._finished.connect(function)
