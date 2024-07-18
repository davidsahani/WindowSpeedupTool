import winreg

import psutil
import win32con
import win32service
import win32serviceutil

from .threads import Error, Result, StatusResult


def start(service_name: str) -> Result[bool]:
    """Start the windows service.

    Return:
        Result(True) on success.
    """
    try:
        win32serviceutil.StartService(service_name)  # type: ignore
    except win32service.error as e:
        return Result(error=Error(e.winerror, e.strerror))
    else:
        return Result(True)


def stop(service_name: str) -> Result[bool]:
    """Stop the windows service.

    Return:
        Result(True) on success.
    """
    try:
        win32serviceutil.StopService(service_name)  # type: ignore
    except win32service.error as e:
        return Result(error=Error(e.winerror, e.strerror))
    else:
        return Result(True)


def net_start(service_name: str) -> StatusResult:
    """Start the windows service using net command."""
    return Result.from_command(
        ["net", "start", service_name, "/y"]
    ).status()


def net_stop(service_name: str) -> StatusResult:
    """Stop the windows service using net command."""
    return Result.from_command(
        ["net", "stop", service_name, "/y"]
    ).status()


def status(service_name: str) -> Result[tuple[int, int, int, int, int, int, int]]:
    """Return status of the windows service."""
    try:
        result = win32serviceutil.QueryServiceStatus(service_name)  # type: ignore # noqa
    except win32service.error as e:
        return Result(error=Error(e.winerror, e.strerror))
    else:
        return Result(result)  # type: ignore


def running() -> tuple[tuple[str, str, tuple[int, int, int, int, int, int, int]], ...]:
    """Get active running services."""
    accessSCM = win32con.GENERIC_READ
    hscm = win32service.OpenSCManager(None, None, accessSCM)
    typeFilter = win32service.SERVICE_WIN32
    stateFilter = win32service.SERVICE_ACTIVE
    return win32service.EnumServicesStatus(hscm, typeFilter, stateFilter)


def services() -> tuple[tuple[str, str, tuple[int, int, int, int, int, int, int]], ...]:
    """Get all windows services."""
    accessSCM = win32con.GENERIC_READ
    hscm = win32service.OpenSCManager(None, None, accessSCM)
    typeFilter = win32service.SERVICE_WIN32
    stateFilter = win32service.SERVICE_STATE_ALL
    return win32service.EnumServicesStatus(hscm, typeFilter, stateFilter)


def info(service_name: str) -> Result[dict[str, str]]:
    """Get information about a Windows service."""
    try:
        result = psutil.win_service_get(service_name).as_dict()  # type: ignore # noqa
    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        return Result(error=Error(e.pid, e.msg))
    except OSError as e:
        return Result(error=Error(e.winerror, e.strerror))
    else:
        return Result(result)  # type: ignore


def service_name(display_name: str) -> Result[str]:
    """Get service name of the windows service."""
    accessSCM = win32con.GENERIC_READ
    hscm = win32service.OpenSCManager(None, None, accessSCM)
    try:
        result = win32service.GetServiceKeyName(hscm, display_name)  # type: ignore # noqa
    except win32service.error as e:
        return Result(error=Error(e.winerror, e.strerror))
    else:
        return Result(result)  # type: ignore


def display_name(service_name: str) -> Result[str]:
    """Get display name of the windows service."""
    accessSCM = win32con.GENERIC_READ
    hscm = win32service.OpenSCManager(None, None, accessSCM)
    try:
        result = win32service.GetServiceDisplayName(hscm, service_name)   # type: ignore # noqa
    except win32service.error as e:
        return Result(error=Error(e.winerror, e.strerror))
    else:
        return Result(result)  # type: ignore


def startup_type(service_name: str) -> Result[str]:
    """Get startup type of the windows service."""
    info_result = info(service_name)
    if info_result.value is None:
        return Result(error=info_result.error)
    start_type = info_result.value['start_type']
    if start_type != 'automatic':
        return Result(start_type)
    # function (info) doesn't account
    # for automatic-delayed startup type.
    result = Result.from_command(
        ["sc", "qc", service_name]
    )
    if result.value is None:
        return Result(error=result.error)
    if "DELAYED" not in result.value:
        return Result("automatic")
    return Result("automatic-delayed")


def set_startup_type(service_name: str, startup_type: str) -> StatusResult:
    """Set startup type of a windows service using sc command.

    Parameters:
        - service_name: The name of the service.
        - startup_type: The startup type of the service.

        This must be `automatic`, `automatic-delayed`, `manual` or `disabled`.

    Raise:
        ValueError: If the startup_type is invalid.
    """
    match startup_type:
        case "automatic":
            start_type = "auto"
        case "automatic-delayed":
            start_type = "delayed-auto"
        case "manual":
            start_type = "demand"
        case "disabled":
            start_type = "disabled"
        case _:
            raise ValueError(f"startup type: {startup_type!r} is invalid.")

    return Result.from_command(["sc", "config", service_name, f"start={start_type}"]).status()


# **************************************************************************
#                         REGISTRY FUNCTIONS                               *
# **************************************************************************


def startup_value(service_name: str) -> Result[int]:
    "Get startup value of the service from windows registry."

    key = winreg.HKEY_LOCAL_MACHINE
    sub_key = "SYSTEM\\CurrentControlSet\\Services"
    reg_path = f"HKEY_LOCAL_MACHINE\\{sub_key}\\{service_name}"

    try:
        reg_key = winreg.OpenKey(key, f"{sub_key}\\{service_name}")

    except FileNotFoundError as e:
        return Result(error=Error(e.winerror, f"{reg_path} doesn't exist."))

    except OSError as e:
        return Result(error=Error(e.winerror, f"{e}\nCouldn't open key: {reg_path}"))

    else:
        try:
            return winreg.QueryValueEx(reg_key, "Start")[0]

        except FileNotFoundError as e:
            return Result(error=Error(e.winerror, f"{reg_path} doesn't exist."))

        except OSError as e:
            return Result(error=Error(e.winerror, f"{e}\nCouldn't read key: {reg_path}"))

        finally:
            winreg.CloseKey(reg_key)


def set_startup_value(service_name: str, startup_type: str) -> Result[bool]:
    """Set startup value of the service in windows registry.

    Parameters:
        - service_name: The name of the service.
        - startup_type: The startup type of the service.

        This must be `automatic`, `automatic-delayed`, `manual` or `disabled`.

    Return:
        Result(True) on success.

    Raise:
        ValueError: If the startup_type is invalid.
    """
    match startup_type:
        case "automatic":
            start_value = 2
        case "automatic-delayed":
            start_value = 2
        case "manual":
            start_value = 3
        case "disabled":
            start_value = 4
        case _:
            raise ValueError(f"startup type: {startup_type!r} is invalid.")

    key = winreg.HKEY_LOCAL_MACHINE
    sub_key = "SYSTEM\\CurrentControlSet\\Services"
    reg_path = f"HKEY_LOCAL_MACHINE\\{sub_key}\\{service_name}"

    try:
        reg_key = winreg.OpenKey(
            key, f"{sub_key}\\{service_name}", 0, winreg.KEY_SET_VALUE)

    except FileNotFoundError as e:
        return Result(error=Error(e.winerror, f"{reg_path} doesn't exist."))

    except OSError as e:
        return Result(error=Error(e.winerror, f"{e}\nCouldn't open key: {reg_path}"))

    else:
        try:
            winreg.SetValueEx(reg_key, "Start", 0, winreg.REG_DWORD, start_value)  # noqa

        except OSError as e:
            return Result(error=Error(e.winerror, f"{e}\nCouldn't write key: {reg_path}"))

        else:
            return Result(True)

        finally:
            winreg.CloseKey(reg_key)
