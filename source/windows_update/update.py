from typing import Iterable
import winreg

from utils import registry, service


def is_any_service_running(service_names: Iterable[str]) -> service.Result[bool]:
    "Check if any service within the provided service_names is currently running."

    last_error: service.Error | None = None

    for service_name in service_names:
        result = service.status(service_name)
        if result.value is None:
            last_error = result.error
        elif result.value[1] in (2, 4):  # starting/running
            return service.Result(True)

    if last_error is None:
        return service.Result(False)
    else:
        return service.Result(error=last_error)


def is_automatic_updates_enabled() -> bool:
    "Check if automatic windows updates is enabled."

    try:
        return not registry.key_value(
            winreg.HKEY_LOCAL_MACHINE,
            "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\WindowsUpdate\\Auto Update",
            "AUOptions"
        )
    except FileNotFoundError:
        return True  # assume True
    except OSError:
        return True  # assume True


def is_automatic_drivers_updates_enabled() -> bool:
    "Check if automatic drivers update on windows update is enabled."

    try:
        return not registry.key_value(
            winreg.HKEY_LOCAL_MACHINE,
            "SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate",
            "ExcludeWUDriversInQualityUpdate"
        )
    except FileNotFoundError:
        return True  # assume True
    except OSError:
        return True  # assume True


def set_automatic_updates(enable: bool) -> None:
    """Set automatic updates in the Windows registry.

    Args:
        enable: True to enable, False to disable.
    """
    key_type = winreg.HKEY_LOCAL_MACHINE
    key_path = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\WindowsUpdate\\Auto Update"
    key_name = "AUOptions"

    if enable:
        try:
            registry.del_key(key_type, key_path, key_name)
        except OSError:
            registry.set_key_value(key_type, key_path, key_name, 0)
    else:
        registry.set_key_value(key_type, key_path, key_name, 1)


def set_automatic_drivers_updates(enable: bool) -> None:
    """Set automatic drivers updates in the Windows registry.

    Args:
        enable: True to enable, False to disable.
    """
    key_type = winreg.HKEY_LOCAL_MACHINE
    key_path = "SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate"
    key_name = "ExcludeWUDriversInQualityUpdate"

    try:
        winreg.OpenKey(key_type, key_path)
    except FileNotFoundError:
        if enable:
            return  # key doesn't exist.
        registry.create_key(  # create the key, if it doesn't exist.
            key_type, "SOFTWARE\\Policies\\Microsoft\\Windows", "WindowsUpdate"
        )

    if enable:
        try:
            registry.del_key(key_type, key_path, key_name)
        except OSError:
            registry.set_key_value(key_type, key_path, key_name, 0)
    else:
        registry.set_key_value(key_type, key_path, key_name, 1)
