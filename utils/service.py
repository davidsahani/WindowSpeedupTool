import subprocess
import winreg
from typing import Generator

import psutil
import win32api
import win32con
import win32process
import win32service
import win32serviceutil

# To hide process console window
PROCESS_STARTUP_INFO = subprocess.STARTUPINFO()
PROCESS_STARTUP_INFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW


def start(service_name: str) -> int:
    """Start the windows service.

    Return:
        0 on success,
        1 on failure
    """
    try:
        win32serviceutil.StartService(service_name)  # type: ignore
    except win32service.error:
        return 1
    else:
        return 0


def stop(service_name: str) -> int:
    """Stop the windows service.

    Return:
        0 on success,
        1 on failure
    """
    try:
        win32serviceutil.StopService(service_name)  # type: ignore
    except win32service.error:
        return 1
    else:
        return 0


def net_start(service_name: str) -> int:
    """Start the windows service using net command.

    Return:
        net process status code
    """
    return subprocess.Popen(
        ["net", "start", service_name, "/y"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        startupinfo=PROCESS_STARTUP_INFO
    ).wait()


def net_stop(service_name: str) -> int:
    """Stop the windows service using net command.

    Return:
        net process status code
    """
    return subprocess.Popen(
        ["net", "stop", service_name, "/y"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        startupinfo=PROCESS_STARTUP_INFO
    ).wait()


def kill(service_name: str) -> None:
    "Kill the windows service."

    # win32serviceutil.StopService(service_name)
    status = win32serviceutil.QueryServiceStatus(service_name)  # type: ignore
    process_id = status[8]  # type: ignore
    handle = win32api.OpenProcess(
        win32con.PROCESS_ALL_ACCESS, False, process_id)  # type: ignore
    win32process.TerminateProcess(handle, 0)
    win32api.CloseHandle(handle)


def status(service_name: str) -> tuple[int, int, int, int, int, int, int]:
    "Return status of the windows service."

    return win32serviceutil.QueryServiceStatus(service_name)  # type: ignore


def display_name(service_name: str) -> str:
    "Return display name of the service."

    accessSCM = win32con.GENERIC_READ
    hscm = win32service.OpenSCManager(None, None, accessSCM)
    return win32service.GetServiceDisplayName(  # type: ignore
        hscm, service_name)


def service_name(display_name: str) -> str:
    "Return service name of the service."

    accessSCM = win32con.GENERIC_READ
    hscm = win32service.OpenSCManager(None, None, accessSCM)
    return win32service.GetServiceKeyName(hscm, display_name)  # type: ignore


def info(service_name: str) -> dict[str, str]:
    "Get information about a Windows service."

    return psutil.win_service_get(service_name).as_dict()  # type: ignore


def startup_type(service_name: str) -> str:
    "Return startup type of the service."

    start_type = info(service_name)['start_type']
    if start_type != 'automatic':
        return start_type
    # function (info) doesn't account
    # for automatic-delayed startup type
    output = subprocess.check_output(
        ["sc", "qc", service_name],
        startupinfo=PROCESS_STARTUP_INFO
    )
    if b"DELAYED" not in output:
        return "automatic"
    return "automatic-delayed"


def running() -> Generator[tuple[str, str, tuple[int]], None, None]:
    "Get running system services."

    accessSCM = win32con.GENERIC_READ
    hscm = win32service.OpenSCManager(None, None, accessSCM)
    typeFilter = win32service.SERVICE_WIN32
    stateFilter = win32service.SERVICE_ACTIVE
    yield from win32service.EnumServicesStatus(  # type: ignore
        hscm, typeFilter, stateFilter)


def services() -> Generator[tuple[str, str, tuple[int]], None, None]:
    "Get all system services."

    accessSCM = win32con.GENERIC_READ
    hscm = win32service.OpenSCManager(None, None, accessSCM)
    typeFilter = win32service.SERVICE_WIN32
    stateFilter = win32service.SERVICE_STATE_ALL
    yield from win32service.EnumServicesStatus(  # type: ignore
        hscm, typeFilter, stateFilter)


def set_startup_type(service_name: str, startup_type: str) -> int:
    """Set startup type of a windows service using sc command.

    Parameters:
    - service_name: The name of the service.
    - startup_type: The startup type of the service.\n
      This must be `automatic`, `automatic-delayed`, `manual` or `disabled`

    Return:
        sc process status code
    """
    match startup_type:
        case 'automatic':
            start_type = 'auto'
        case 'automatic-delayed':
            start_type = 'delayed-auto'
        case 'manual':
            start_type = 'demand'
        case 'disabled':
            start_type = 'disabled'
        case _:
            raise ValueError(f"{startup_type!r}, startup type is invalid")

    cmd = ["sc", "config", service_name, "start=", start_type]
    return subprocess.Popen(
        cmd, stdout=subprocess.DEVNULL, startupinfo=PROCESS_STARTUP_INFO).wait()


# **************************************************************************
#                         REGISTRY FUNCTIONS                               *
# **************************************************************************


def startup_value(service_name: str) -> int:
    "Return startup value of the windows service"

    key_type = winreg.HKEY_LOCAL_MACHINE
    key_path = r"SYSTEM\CurrentControlSet\Services"

    reg_key = winreg.OpenKey(key_type, fr"{key_path}\{service_name}")
    try:
        return winreg.QueryValueEx(reg_key, "Start")[0]
    finally:
        winreg.CloseKey(reg_key)


def set_startup_value(service_name: str, start_value: int) -> int:
    """Set startup value of the windows service

    Return:
        0 on success,
        1 on failure
    """

    key_type = winreg.HKEY_LOCAL_MACHINE
    key_path = r"SYSTEM\CurrentControlSet\Services"

    key = winreg.OpenKey(
        key_type, fr"{key_path}\{service_name}", 0, winreg.KEY_SET_VALUE)
    try:
        winreg.SetValueEx(key, "Start", 0, winreg.REG_DWORD, start_value)
    except OSError:
        return 1
    else:
        return 0
    finally:
        winreg.CloseKey(key)


# ? LAME WIN32 FUNCTION, doesn't support auto-delayed startup type
def _set_startup_type(service_name: str, startup_type: int) -> int:
    """Set the startup type of a windows service.

    Parameters:
    - service_name: The name of the service.
    - startup_type: The startup type of the service.\
      This should be an integer constant from the win32service module,
      such as SERVICE_AUTO_START for "Automatic" startup or SERVICE_DEMAND_START for "Manual" startup.

    Return:
        0 on success, 1 on failure
    """
    try:
        # Open the service
        hscm = win32service.OpenSCManager(
            None, None, win32service.SC_MANAGER_ALL_ACCESS)
        hs = win32service.OpenService(  # type: ignore
            hscm, service_name, win32service.SERVICE_ALL_ACCESS)

        # Set the startup type
        win32service.ChangeServiceConfig(  # type: ignore
            hs, win32service.SERVICE_NO_CHANGE, startup_type,
            win32service.SERVICE_NO_CHANGE, None, None, False, None, None, None, None)
        # Close the service
        win32service.CloseServiceHandle(hs)
        win32service.CloseServiceHandle(hscm)
    except win32service.error:
        return 1
    else:
        return 0
