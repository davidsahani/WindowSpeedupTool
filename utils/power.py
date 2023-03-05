import os
import re
import subprocess
import winreg

import psutil

from .registry import create_key, del_key, key_value, set_key_value

DEFAULT_SCHEME_GUIDS = [
    "381b4222-f694-41f0-9685-ff5bb260df2e",
    "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
    "a1841308-3541-4fab-bc81-f71556f20b4a"
]

GUID_PATTERN = "[a-zA-Z0-9]{8}-[a-zA-Z0-9]{4}"\
    "-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{12}"

# To hide process console window
PROCESS_STARTUP_INFO = subprocess.STARTUPINFO()
PROCESS_STARTUP_INFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW


def schemes() -> list[tuple[str, str]]:
    "Return list of all the power schemes"

    result: list[tuple[str, str]] = []
    output = subprocess.check_output(
        ["powercfg", "-list"],
        startupinfo=PROCESS_STARTUP_INFO
    )
    for line in output.decode().splitlines():
        guid = re.findall(GUID_PATTERN, line)
        name = re.findall(r'\(([^\)]+)\)', line)
        if not name or not guid:
            continue
        result.append((name[0], guid[0]))
    return result


def aliases() -> dict[str, str]:
    "Return aliases and their corresponding GUIDs"

    result: dict[str, str] = {}
    output = subprocess.check_output(
        ["powercfg", "-aliases"], startupinfo=PROCESS_STARTUP_INFO
    )
    for line in filter(None, output.decode().splitlines()):
        guid, alias = line.split()
        result[alias] = guid
    return result


def active() -> tuple[str, str]:
    "Return the active power scheme name and GUID"

    output = subprocess.check_output(
        ["powercfg", "-getactivescheme"],
        startupinfo=PROCESS_STARTUP_INFO).decode()

    return (re.findall(r'\(([^\)]+)\)', output)[0],
            re.findall(GUID_PATTERN, output)[0])


def set_active(guid: str) -> int:
    "Set this GUID as active power scheme"

    cmd = ["powercfg", "-setactive", guid]
    return subprocess.Popen(cmd, startupinfo=PROCESS_STARTUP_INFO).wait()


def change_name(guid: str, name: str, description: str = "") -> int:
    "Change name and description of the given GUID"

    cmd = ["powercfg", "-changename", guid, name]
    _ = description and cmd.append(description)
    return subprocess.Popen(cmd, startupinfo=PROCESS_STARTUP_INFO).wait()


def duplicate_scheme(scheme_guid: str, destination_guid: str = "") -> tuple[str, str]:
    """Duplicate an existing power scheme.

    Args:
        scheme_guid: The GUID of the power scheme to duplicate.
        destination_guid: Specifies the new power scheme's GUID.
        If no GUID is specified, create a new GUID.

    Return
        The power scheme representing the new power scheme.
    """

    cmd = ["powercfg", "-duplicatescheme", scheme_guid]
    _ = destination_guid and cmd.append(destination_guid)

    output = subprocess.check_output(
        cmd, startupinfo=PROCESS_STARTUP_INFO).decode()
    return (re.findall(r'\(([^\)]+)\)', output)[0],
            re.findall(GUID_PATTERN, output)[0])


def delete_scheme(guid: str) -> int:
    "Delete power scheme associated with GUID"

    cmd = ["powercfg", "-d", guid]
    return subprocess.Popen(cmd, startupinfo=PROCESS_STARTUP_INFO).wait()


def change_setting_value(setting: str, value: int) -> int:
    """Modify a setting value in the current power scheme

    Parameter List:
        <SETTING>    Specifies one of the following options:

        monitor-timeout-ac
        monitor-timeout-dc
        disk-timeout-ac
        disk-timeout-dc
        standby-timeout-ac
        standby-timeout-dc
        hibernate-timeout-ac
        hibernate-timeout-dc

    <VALUE>      Specifies the new value, in minutes.
    """
    cmd = ["powercfg", "-change", setting, str(value)]
    return subprocess.Popen(cmd, startupinfo=PROCESS_STARTUP_INFO).wait()


def import_scheme(filepath: str, guid: str = "") -> int:
    "Import a power scheme file from the given path and GUID"

    cmd = ["powercfg", "-import", filepath]
    _ = guid and cmd.append(guid)
    return subprocess.Popen(
        cmd, stdout=subprocess.DEVNULL,
        startupinfo=PROCESS_STARTUP_INFO
    ).wait()


def export_scheme(filepath: str, guid: str) -> int:
    "Export a power scheme of the given GUID to path"

    cmd = ["powercfg", "-export", filepath, guid]
    return subprocess.Popen(cmd, startupinfo=PROCESS_STARTUP_INFO).wait()


def set_active_by_name(scheme_name: str) -> int:
    "Set power scheme active by name"

    guids = [guid for name, guid in schemes() if name == scheme_name]
    if not guids:
        raise ValueError(f"{scheme_name!r} doesn't exist")
    return set_active(guids[0])  # set the first scheme found


def list_powerthrottling() -> list[str]:
    "List all powerthrottling disabled applications"

    cmd = ["powercfg", "powerthrottling", "list"]
    output = subprocess.check_output(cmd, startupinfo=PROCESS_STARTUP_INFO)
    return re.findall(": (.*).", output.decode())


def disable_powerthrottling(program: str) -> int:
    "Disable powerthrottling of the application"

    if not os.path.isfile(program):
        cmd = ["powercfg", "powerthrottling", "disable", "/pfn", program]
    else:
        cmd = ["powercfg", "powerthrottling", "disable", "/path", program]
    return subprocess.Popen(cmd, startupinfo=PROCESS_STARTUP_INFO).wait()


def reset_powerthrottling(program: str) -> int:
    "Reset powerthrottling of the application"

    if not os.path.isfile(program):
        cmd = ["powercfg", "powerthrottling", "reset", "/pfn", program]
    else:
        cmd = ["powercfg", "powerthrottling", "reset", "/path", program]
    return subprocess.Popen(cmd, startupinfo=PROCESS_STARTUP_INFO).wait()


# **************************************************************************
# ADDITIONAL FUNCTIONS  and helpers                                  *
# **************************************************************************


def launch_advanced_settings() -> None:
    "Launch Advanced power settings"

    cmd = "control powercfg.cpl,,1"
    subprocess.Popen(cmd, startupinfo=PROCESS_STARTUP_INFO)


def get_display_timeout(scheme_guid: str) -> tuple[int, int]:
    """Get display timeout in minutes

    Return:
        AC Power Timeout,
        DC Power Timeout
    """

    guid = aliases()['SUB_VIDEO']
    cmd = ["powercfg", "/query", scheme_guid, guid]
    output = subprocess.check_output(
        cmd, startupinfo=PROCESS_STARTUP_INFO).decode()

    ac_value = re.findall(
        r"Current AC Power Setting Index: ([a-z-0-9]*)", output)[0]
    dc_value = re.findall(
        r"Current DC Power Setting Index: ([a-z-0-9]*)", output)[0]
    return int(ac_value, 0) // 60, int(dc_value, 0) // 60


def get_sleep_timeout(scheme_guid: str) -> tuple[int, int]:
    """Get sleep timeout in minutes

    Return:
        AC Power Timeout,
        DC Power Timeout
    """

    guid = aliases()['SUB_SLEEP']
    cmd = ["powercfg", "/query", scheme_guid, guid]
    output = subprocess.check_output(
        cmd, startupinfo=PROCESS_STARTUP_INFO).decode()

    ac_value = re.findall(
        r"Current AC Power Setting Index: ([a-z-0-9]*)", output)[0]
    dc_value = re.findall(
        r"Current DC Power Setting Index: ([a-z-0-9]*)", output)[0]
    return int(ac_value, 0) // 60, int(dc_value, 0) // 60


def query(scheme_guid: str, sub_guid: str = ""):
    "Return all power profile text for specific scheme"

    cmd = ["powercfg", "-query", scheme_guid]
    _ = sub_guid and cmd.append(sub_guid)
    output = subprocess.check_output(cmd, startupinfo=PROCESS_STARTUP_INFO)
    return output.decode()


def enable_hibernation() -> int:
    "Enable system hibernation"

    cmd = ["powercfg", "-h", "on"]
    return subprocess.Popen(cmd, startupinfo=PROCESS_STARTUP_INFO).wait()


def disable_hibernation() -> int:
    "Disable system hibernation"

    cmd = ["powercfg", "-h", "off"]
    return subprocess.Popen(cmd, startupinfo=PROCESS_STARTUP_INFO).wait()


def restart(force_restart: bool = False) -> int:
    "Restart the system without delay"

    if force_restart:
        cmd = ["shutdown", "/r", "/f"]
    else:
        cmd = ["shutdown", "/r", "/t", "0"]
    return subprocess.Popen(cmd, startupinfo=PROCESS_STARTUP_INFO).wait()

# **************************************************************************
# FUNCTIONS FOR BATTERY                                                    *
# **************************************************************************


def has_battery() -> bool:
    """
    Check if the device has a battery.

    Return:
        bool: True if the device has a battery, False if it does not.
    """

    return psutil.sensors_battery() is not None  # type: ignore


def get_estimated_charge_remaining():
    "Return a number representing the current % of charge. If the laptop is charging will return 111"

    output = subprocess.check_output(
        ["WMIC", "Path", "Win32_Battery", "Get", "EstimatedChargeRemaining"],
        startupinfo=PROCESS_STARTUP_INFO).strip()
    return output.decode().split()


def get_estimated_run_time():
    "Return a number representing the number of minutes of battery life remaining."

    output = subprocess.check_output(
        ["WMIC", "Path", "Win32_Battery", "Get", "EstimatedRunTime"],
        startupinfo=PROCESS_STARTUP_INFO).strip()
    return output.decode().split()


# **************************************************************************
# REGISTRY FUNCTIONS                                                    *
# **************************************************************************


def is_gamemode_enabled() -> bool:
    try:
        return not not key_value(
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\GameBar",
            "AutoGameModeEnabled"
        )
    except ValueError:
        return True  # assume True
    except OSError:
        return True  # assume True


def is_fast_startup_enabled() -> bool:
    try:
        return not not key_value(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Power",
            "HiberbootEnabled"
        )
    except ValueError:
        return True  # assume True
    except OSError:
        return True  # assume True


def is_hibernation_enabled() -> bool:
    try:
        return not not key_value(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Power",
            "HibernateEnabled"
        )
    except ValueError:
        return True  # assume True
    except OSError:
        return True  # assume True


def is_usb_power_saving_enabled() -> bool:
    try:
        return not key_value(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Services\USB",
            "DisableSelectiveSuspend"
        )
    except ValueError:
        return True  # assume True
    except OSError:
        return True  # assume True


def is_powerthrottling_enabled() -> bool:
    try:
        return not key_value(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Power\PowerThrottling",
            "PowerThrottlingOff"
        )
    except ValueError:
        return True  # assume True
    except OSError:
        return True  # assume True


def set_gamemode(enable: bool) -> int:
    """Enable gamemode feature in the
    registry, if `enable` is True else Disable.

    Return:
        0 on success,
        1 on failure
    """

    key_type = winreg.HKEY_CURRENT_USER
    key_path = r"SOFTWARE\Microsoft\GameBar"
    key_name = "AutoGameModeEnabled"

    if enable:
        if status := del_key(key_type, key_path, key_name):
            return set_key_value(key_type, key_path, key_name, 1)
        return status
    return set_key_value(key_type, key_path, key_name, 0)


def set_fast_startup(enable: bool) -> int:
    """Enable fast startup feature in the
    registry, if `enable` is True else Disable.

    Return:
        0 on success,
        1 on failure
    """

    key_type = winreg.HKEY_LOCAL_MACHINE
    key_path = r"SYSTEM\CurrentControlSet\Control\Session Manager\Power"
    key_name = "HiberbootEnabled"

    if enable:
        return set_key_value(key_type, key_path, key_name, 1)
    return set_key_value(key_type, key_path, key_name, 0)


def set_hibernation(enable: bool) -> int:
    """Enable hibernation feature in the
    registry, if `enable` is True else Disable.

    Return:
        0 on success,
        1 on failure
    """

    key_type = winreg.HKEY_LOCAL_MACHINE
    key_path = r"SYSTEM\CurrentControlSet\Control\Power"
    key_name = "HibernateEnabled"

    if enable:
        if status := del_key(key_type, key_path, key_name):
            return set_key_value(key_type, key_path, key_name, 1)
        return status
    return set_key_value(key_type, key_path, key_name, 0)


def set_usb_power_saving(enable: bool) -> int:
    """Enable usb power saving feature in the
    registry, if `enable` is True else Disable.

    Return:
        0 on success,
        1 on failure,
        2 when failed to create key
    """

    key_type = winreg.HKEY_LOCAL_MACHINE
    key_path = r"SYSTEM\CurrentControlSet\Services"
    key_name = "USB"

    if enable:
        return del_key(key_type, key_path, key_name)

    status = create_key(key_type, key_path, key_name)
    if status:
        return 2
    return set_key_value(
        key_type,
        key_path + fr"\{key_name}",
        "DisableSelectiveSuspend",
        1
    )


def set_power_throttling(enable: bool) -> int:
    """Enable power throttling feature in the
    registry, if `enable` is True else Disable.

    Return:
        0 on success,
        1 on failure,
        2 when failed to create key
    """

    key_type = winreg.HKEY_LOCAL_MACHINE
    key_path = r"SYSTEM\CurrentControlSet\Control\Power"
    key_name = "PowerThrottling"

    if enable:
        return del_key(key_type, key_path, key_name)

    status = create_key(key_type, key_path, key_name)
    if status:
        return 2
    return set_key_value(
        key_type,
        key_path + fr"\{key_name}",
        "PowerThrottlingOff",
        1
    )
