from enum import Enum
from typing import Any, Callable, Concatenate, override, ParamSpec, TypeAlias

from PyQt6.QtCore import pyqtSignal, QMutex, QMutexLocker, QObject, QThread

from utils import service
from utils.config_parser import Service

P = ParamSpec('P')

ServicesType: TypeAlias = list[Service]
FailedServicesType: TypeAlias = list[tuple[Service, str]]


class Action(Enum):
    START = "start"
    STOP = "stop"
    ENABLE = "enable"
    DISABLE = "disable"


class ServicesThread(QThread):
    progress = pyqtSignal(int)
    _finished = pyqtSignal(Action, list, bool)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._init_attrs()
        self.finished.connect(lambda: (
            self._finished.emit(
                self.__action,
                self.__failed_services,
                self.__restart_required
            ),
            self._init_attrs()
        ))
        self.__mutex = QMutex()
        self.__pre_disable_func_args = None

    def _init_attrs(self) -> None:
        self.__action = None
        self.__function = None
        self.__services = None
        self.__cancel_flag: bool = False
        self.__restart_required: bool = False
        self.__failed_services: FailedServicesType = []

    @override
    def start(self, action: Action, services: ServicesType) -> None:  # pyright: ignore[reportIncompatibleMethodOverride] # noqa
        """Start thread to perform specified action for services."""
        match action:
            case Action.START:
                self.__function = self.startServices
            case Action.STOP:
                self.__function = self.stopServices
            case Action.ENABLE:
                self.__function = self.enableServices
            case Action.DISABLE:
                self.__function = self.disableServices

        self.__action = action
        self.__services = services
        self.__failed_services = []
        self.__restart_required = False
        super().start()

    def connectFinished(self, function: Callable[[Action, FailedServicesType, bool], Any]) -> None:
        """Connect the function to thread finish event.

        Receive:
            Action, Failed Services: list[tuple[service, error]], Restart Required.
        """
        self._finished.connect(function)

    def connectPreDisable(self, func: Callable[Concatenate[P], Any], *args: P.args, **kwargs: P.kwargs) -> None:
        """Connect a function to be executed before disabling services in a new thread."""
        with QMutexLocker(self.__mutex):
            self.__pre_disable_func_args = func, args, kwargs

    def cancel(self) -> None:
        with QMutexLocker(self.__mutex):
            self.__cancel_flag = True

    def is_cancelled(self) -> bool:
        with QMutexLocker(self.__mutex):
            return self.__cancel_flag

    def reset_cancel(self) -> None:
        with QMutexLocker(self.__mutex):
            self.__cancel_flag = False

    @override
    def run(self) -> None:
        self.reset_cancel()
        if self.__function is None or \
                self.__services is None:
            return
        self.__function(self.__services)

    def startServices(self, services: ServicesType) -> None:
        for value, svc in enumerate(services, start=1):
            if self.is_cancelled():
                break
            self.progress.emit(value)

            status_result = service.status(svc.service_name)
            if status_result.value is None:
                self.__failed_services.append(
                    (svc, status_result.error.stderr)
                )
                continue

            if status_result.value[1] == 4:
                continue  # already running

            if service.start(svc.service_name).success:
                continue  # on success

            result = service.net_start(svc.service_name)
            if result.status == 0:
                continue  # on success

            self.__failed_services.append((svc, result.error))

    def stopServices(self, services: ServicesType) -> None:
        for value, svc in enumerate(services, start=1):
            if self.is_cancelled():
                break
            self.progress.emit(value)

            status_result = service.status(svc.service_name)
            if status_result.value is None:
                self.__failed_services.append(
                    (svc, status_result.error.stderr)
                )
                continue

            if status_result.value[1] != 4:
                continue  # already stopped

            if service.stop(svc.service_name).success:
                continue  # on success

            result = service.net_stop(svc.service_name)
            if result.status == 0:
                continue  # on success

            self.__failed_services.append((svc, result.error))

    def enableServices(self, services: ServicesType) -> None:
        for value, svc in enumerate(services, start=1):
            if self.is_cancelled():
                break
            self.progress.emit(value)

            info_result = service.info(svc.service_name)
            if info_result.value is None:
                self.__failed_services.append(
                    (svc, info_result.error.stderr)
                )
                continue

            if info_result.value['start_type'] != 'disabled':
                continue  # already enabled

            try:
                result = service.set_startup_type(
                    svc.service_name, svc.startup_type
                )
            except ValueError as e:
                self.__failed_services.append((svc, str(e)))
                continue

            if result.status == 0:
                continue  # on success

            # Access is denied or RPC service is unavailable or dependency not started.
            if result.status in (5, 1722, 3221356598):
                result = service.set_startup_value(
                    svc.service_name, svc.startup_type
                )
                if result.status == 0:
                    self.__restart_required = True
                    continue

            self.__failed_services.append((svc, result.error))

    def disableServices(self, services: ServicesType) -> None:
        # execute callback before disabling services.
        if self.__pre_disable_func_args is not None:
            func, args, kwargs = self.__pre_disable_func_args
            func(*args, **kwargs)

        for value, svc in enumerate(services, start=1):
            if self.is_cancelled():
                break
            self.progress.emit(value)

            info_result = service.info(svc.service_name)
            if info_result.value is None:
                self.__failed_services.append(
                    (svc, info_result.error.stderr)
                )
                continue

            if info_result.value['start_type'] == 'disabled':
                continue  # already disabled

            try:
                result = service.set_startup_type(svc.service_name, 'disabled')
            except ValueError as e:
                self.__failed_services.append((svc, str(e)))
                continue

            if result.status == 0:
                continue  # on success

            # Access is denied or RPC service is unavailable.
            if result.status in (5, 1722):
                result = service.set_startup_value(
                    svc.service_name, 'disabled'
                )
                if result.status == 0:
                    self.__restart_required = True
                    continue

            self.__failed_services.append((svc, result.error))
