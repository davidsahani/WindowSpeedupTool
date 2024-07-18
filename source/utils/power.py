import os
import re
import winreg

from .registry import create_key, del_key, key_value, set_key_value
from .threads import Result, StatusResult

DEFAULT_SCHEME_GUIDS = [
    "381b4222-f694-41f0-9685-ff5bb260df2e",  # Balanced
    "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",  # High Performance
    "a1841308-3541-4fab-bc81-f71556f20b4a"   # Power Saver
]

GUID_PATTERN = "[a-zA-Z0-9]{8}-[a-zA-Z0-9]{4}" + \
    "-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{12}"


def schemes() -> Result[list[tuple[str, str]]]:
    "Get list of all the power schemes."

    cmd = ["powercfg", "-list"]
    proc_result = Result.from_command(cmd)
    if proc_result.value is None:
        return Result(error=proc_result.error)

    result: list[tuple[str, str]] = []
    for line in proc_result.value.splitlines():
        guids = re.findall(GUID_PATTERN, line)
        names = re.findall(r'\(([^\)]+)\)', line)
        if not names or not guids:
            continue
        result.append((names[0], guids[0]))

    return Result(result)


def aliases() -> Result[dict[str, str]]:
    "Get aliases and their corresponding GUIDs."

    cmd = ["powercfg", "-aliases"]
    proc_result = Result.from_command(cmd)
    if proc_result.value is None:
        return Result(error=proc_result.error)

    result: dict[str, str] = {}
    for line in filter(None, proc_result.value.splitlines()):
        guid, alias = line.split()
        result[alias] = guid

    return Result(result)


def active() -> Result[tuple[str, str]]:
    "Get the active power scheme name and GUID."

    cmd = ["powercfg", "-getactivescheme"]
    proc_result = Result.from_command(cmd)
    if proc_result.value is None:
        return Result(error=proc_result.error)

    names = re.findall(r'\(([^\)]+)\)', proc_result.value)
    guids = re.findall(GUID_PATTERN, proc_result.value)
    return Result(((names or [''])[0], (guids or [''])[0]))


def set_active(guid: str) -> StatusResult:
    "Set this GUID as active power scheme."

    cmd = ["powercfg", "-setactive", guid]
    return Result.from_command(cmd).status()


def change_name(guid: str, name: str, description: str = "") -> StatusResult:
    "Change name and description of the given GUID."

    cmd = ["powercfg", "-changename", guid, name]
    _ = description and cmd.append(description)
    return Result.from_command(cmd).status()


def duplicate_scheme(scheme_guid: str, destination_guid: str = "") -> Result[tuple[str, str]]:
    """Duplicate an existing power scheme.

    Parameters:
        - scheme_guid: The GUID of the power scheme to duplicate.
        - destination_guid: Specifies the new power scheme's GUID.
        If no GUID is specified, create a new GUID.

    Return:
        The power scheme representing the new power scheme.
    """
    cmd = ["powercfg", "-duplicatescheme", scheme_guid]
    _ = destination_guid and cmd.append(destination_guid)

    proc_result = Result.from_command(cmd)
    if proc_result.value is None:
        return Result(error=proc_result.error)

    names = re.findall(r'\(([^\)]+)\)', proc_result.value)
    guids = re.findall(GUID_PATTERN, proc_result.value)
    return Result(((names or [''])[0], (guids or [''])[0]))


def delete_scheme(guid: str) -> StatusResult:
    "Delete power scheme associated with GUID."

    cmd = ["powercfg", "-delete", guid]
    return Result.from_command(cmd).status()


def change_setting_value(setting: str, value: int) -> StatusResult:
    """Modify a setting value in the current power scheme.

    Parameter List:
        <SETTING> Specify one of the following options:

        monitor-timeout-ac \n
        monitor-timeout-dc \n
        disk-timeout-ac \n
        disk-timeout-dc \n
        standby-timeout-ac \n
        standby-timeout-dc \n
        hibernate-timeout-ac \n
        hibernate-timeout-dc \n

    <VALUE> Specify the new value, in minutes.
    """
    cmd = ["powercfg", "-change", setting, str(value)]
    return Result.from_command(cmd).status()


def import_scheme(filepath: str, guid: str = "") -> StatusResult:
    """Import a power scheme from the specified file.

    Parameters:
        - filepath: fully-qualified path to the scheme file.
        - guid: GUID for the imported scheme.
        If no GUID is specified, a new GUID will be created.
    """
    cmd = ["powercfg", "-import", filepath]
    _ = guid and cmd.append(guid)
    return Result.from_command(cmd).status()


def export_scheme(filepath: str, guid: str) -> StatusResult:
    """Export a power scheme, represented by the specified GUID, to the specified file.

    Parameters:
        - filepath: fully-qualified path to destination file.
        - guid: The GUID of the power scheme to export.
    """
    cmd = ["powercfg", "-export", filepath, guid]
    return Result.from_command(cmd).status()


def list_powerthrottling() -> Result[list[str]]:
    "List all powerthrottling disabled applications."

    cmd = ["powercfg", "powerthrottling", "list"]
    result = Result.from_command(cmd)
    if result.value is None:
        return Result(error=result.error)
    return Result(re.findall(": (.*).", result.value))


def disable_powerthrottling(program: str) -> StatusResult:
    "Disable powerthrottling of the application."

    if not os.path.isfile(program):
        cmd = ["powercfg", "powerthrottling", "disable", "/pfn", program]
    else:
        cmd = ["powercfg", "powerthrottling", "disable", "/path", program]
    return Result.from_command(cmd).status()


def reset_powerthrottling(program: str) -> StatusResult:
    "Reset powerthrottling of the application."

    if not os.path.isfile(program):
        cmd = ["powercfg", "powerthrottling", "reset", "/pfn", program]
    else:
        cmd = ["powercfg", "powerthrottling", "reset", "/path", program]
    return Result.from_command(cmd).status()


def get_display_timeout(scheme_guid: str) -> Result[tuple[int, int]]:
    """Get scheme display timeout in minutes.

    Return:
        AC Power Timeout, DC Power Timeout.
    """
    aliases_result = aliases()
    if aliases_result.value is None:
        return Result(error=aliases_result.error)

    guid = aliases_result.value['SUB_VIDEO']
    cmd = ["powercfg", "/query", scheme_guid, guid]
    query_result = Result.from_command(cmd)

    if query_result.value is None:
        return Result(error=query_result.error)

    ac_value = re.findall(
        r"Current AC Power Setting Index: ([a-z-0-9]*)", query_result.value)[0]
    dc_value = re.findall(
        r"Current DC Power Setting Index: ([a-z-0-9]*)", query_result.value)[0]

    return Result((int(ac_value, 0) // 60, int(dc_value, 0) // 60))


def get_sleep_timeout(scheme_guid: str) -> Result[tuple[int, int]]:
    """Get scheme sleep timeout in minutes.

    Return:
        AC Power Timeout, DC Power Timeout.
    """
    aliases_result = aliases()
    if aliases_result.value is None:
        return Result(error=aliases_result.error)

    guid = aliases_result.value['SUB_SLEEP']
    cmd = ["powercfg", "/query", scheme_guid, guid]
    query_result = Result.from_command(cmd)

    if query_result.value is None:
        return Result(error=query_result.error)

    ac_value = re.findall(
        r"Current AC Power Setting Index: ([a-z-0-9]*)", query_result.value)[0]
    dc_value = re.findall(
        r"Current DC Power Setting Index: ([a-z-0-9]*)", query_result.value)[0]

    return Result((int(ac_value, 0) // 60, int(dc_value, 0) // 60))


def enable_hibernation() -> StatusResult:
    "Enable system hibernation."

    cmd = ["powercfg", "-h", "on"]
    return Result.from_command(cmd).status()


def disable_hibernation() -> StatusResult:
    "Disable system hibernation."

    cmd = ["powercfg", "-h", "off"]
    return Result.from_command(cmd).status()


def restart(force_restart: bool = False) -> StatusResult:
    "Restart the system without delay."

    if force_restart:
        cmd = ["shutdown", "/r", "/f"]
    else:
        cmd = ["shutdown", "/r", "/t", "0"]
    return Result.from_command(cmd).status()


def launch_advanced_settings() -> StatusResult:
    "Launch Advanced power settings."

    cmd = ["control", "powercfg.cpl,,1"]
    return Result.from_command(cmd).status()


# **************************************************************************
# *                         REGISTRY FUNCTIONS                             *
# **************************************************************************


def is_gamemode_enabled() -> bool:
    "Check if gamemode is enabled within registry."

    try:
        return not not key_value(
            winreg.HKEY_CURRENT_USER,
            "SOFTWARE\\Microsoft\\GameBar",
            "AutoGameModeEnabled"
        )
    except FileNotFoundError:
        return True  # assume True
    except OSError:
        return True  # assume True


def is_fast_startup_enabled() -> bool:
    "Check if fast startup is enabled within registry."

    try:
        return not not key_value(
            winreg.HKEY_LOCAL_MACHINE,
            "SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power",
            "HiberbootEnabled"
        )
    except FileNotFoundError:
        return True  # assume True
    except OSError:
        return True  # assume True


def is_hibernation_enabled() -> bool:
    "Check if hibernation is enabled within registry."

    try:
        return not not key_value(
            winreg.HKEY_LOCAL_MACHINE,
            "SYSTEM\\CurrentControlSet\\Control\\Power",
            "HibernateEnabled"
        )
    except FileNotFoundError:
        return True  # assume True
    except OSError:
        return True  # assume True


def is_usb_power_saving_enabled() -> bool:
    "Check if usb power saving is enabled within registry."

    try:
        return not key_value(
            winreg.HKEY_LOCAL_MACHINE,
            "SYSTEM\\CurrentControlSet\\Services\\USB",
            "DisableSelectiveSuspend"
        )
    except FileNotFoundError:
        return True  # assume True
    except OSError:
        return True  # assume True


def is_powerthrottling_enabled() -> bool:
    "Check if power throttling is enabled within registry."

    try:
        return not key_value(
            winreg.HKEY_LOCAL_MACHINE,
            "SYSTEM\\CurrentControlSet\\Control\\Power\\PowerThrottling",
            "PowerThrottlingOff"
        )
    except FileNotFoundError:
        return True  # assume True
    except OSError:
        return True  # assume True


def set_gamemode(enable: bool) -> None:
    """Set Game Mode in the Windows registry.

    Args:
        enable: True to enable, False to disable.
    """
    key = winreg.HKEY_CURRENT_USER
    sub_key = "SOFTWARE\\Microsoft\\GameBar"
    name = "AutoGameModeEnabled"

    if enable:
        try:
            del_key(key, sub_key, name)
        except OSError:
            set_key_value(key, sub_key, name, 1)
    else:
        set_key_value(key, sub_key, name, 0)


def set_fast_startup(enable: bool) -> None:
    """Set fast startup in the Windows registry.

    Args:
        enable: True to enable, False to disable.
    """
    key = winreg.HKEY_LOCAL_MACHINE
    sub_key = "SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power"
    name = "HiberbootEnabled"

    if enable:
        set_key_value(key, sub_key, name, 1)
    else:
        set_key_value(key, sub_key, name, 0)


def set_hibernation(enable: bool) -> None:
    """Set hibernation in the Windows registry.

    Args:
        enable: True to enable, False to disable.
    """
    key = winreg.HKEY_LOCAL_MACHINE
    sub_key = "SYSTEM\\CurrentControlSet\\Control\\Power"
    name = "HibernateEnabled"

    if enable:
        try:
            del_key(key, sub_key, name)
        except OSError:
            set_key_value(key, sub_key, name, 1)
    else:
        set_key_value(key, sub_key, name, 0)


def set_usb_power_saving(enable: bool) -> None:
    """Set usb power saving in the Windows registry.

    Args:
        enable: True to enable, False to disable.
    """
    key = winreg.HKEY_LOCAL_MACHINE
    sub_key = "SYSTEM\\CurrentControlSet\\Services"
    name = "USB"

    if enable:
        return del_key(key, sub_key, name)

    create_key(key, sub_key, name)
    set_key_value(
        key,
        sub_key + fr"\{name}",
        "DisableSelectiveSuspend",
        1
    )


def set_power_throttling(enable: bool) -> None:
    """Set power throttling in the Windows registry.

    Args:
        enable: True to enable, False to disable.
    """
    key = winreg.HKEY_LOCAL_MACHINE
    sub_key = "SYSTEM\\CurrentControlSet\\Control\\Power"
    name = "PowerThrottling"

    if enable:
        return del_key(key, sub_key, name)

    create_key(key, sub_key, name)
    set_key_value(
        key,
        sub_key + fr"\{name}",
        "PowerThrottlingOff",
        1
    )
