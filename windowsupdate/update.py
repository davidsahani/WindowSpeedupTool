import json
import os
import winreg
from typing import Iterable

from utils import config, registry, service


def is_services_running(service_names: Iterable[str]) -> bool:
    "Check if any windows update services are running."

    return any(
        (service.status(svc)[1] == 4 for svc in service_names)
    )


def is_automatic_updates_enabled() -> bool:
    "Check if automatic windows updates is enabled."

    try:
        return not registry.key_value(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update",
            "AUOptions"
        )
    except ValueError:
        return True  # assume True
    except OSError:
        return True  # assume True


def is_automatic_drivers_updates_enabled() -> bool:
    "Check if automatic drivers update on windows update is enabled."

    try:
        return not registry.key_value(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate",
            "ExcludeWUDriversInQualityUpdate"
        )
    except ValueError:
        return True  # assume True
    except OSError:
        return True  # assume True


def set_automatic_updates(enable: bool) -> int:
    """Enable automatic updates,
    if `enable` is True else Disable

    Return:
        0 on success, 1 on failure
    """

    key_type = winreg.HKEY_LOCAL_MACHINE
    key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update"
    key_name = "AUOptions"

    if enable:
        if status := registry.del_key(key_type, key_path, key_name):
            return registry.set_key_value(key_type, key_path, key_name, 0)
        return status
    return registry.set_key_value(key_type, key_path, key_name, 1)


def set_automatic_drivers_updates(enable: bool) -> int:
    """Enable automatic drivers updates,
    if `enable` is True else Disable

    Return:
        0 on success, 1 on failure
    """

    key_type = winreg.HKEY_LOCAL_MACHINE
    key_path = r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate"
    key_name = "ExcludeWUDriversInQualityUpdate"

    try:
        winreg.OpenKey(key_type, key_path)
    except FileNotFoundError:
        registry.create_key(  # create the key, if doesn't exist
            key_type, r"SOFTWARE\Policies\Microsoft\Windows", "WindowsUpdate")

    if enable:
        if status := registry.del_key(key_type, key_path, key_name):
            return registry.set_key_value(key_type, key_path, key_name, 0)
        return status
    return registry.set_key_value(key_type, key_path, key_name, 1)


# **************************************************************************
#                   CONFIGURATION LOADING AND BACKUP                       *
# **************************************************************************

WINDOWS_SERVICES_CONFIG = "update_services.json"


def _load(filepath: str) -> dict[str, list[str]]:
    "Load service configuration from a JSON file."

    with open(filepath) as file:
        services_config = json.load(file)
    return services_config


def load_config(filename: str) -> dict[str, list[str]]:
    """Load the windows update services config from json file.

    Return:
        merge of default and backup config if backup file exists.
    """

    default_file = os.path.join(config.DEFAULT_DIR, filename)
    backup_file = os.path.join(config.BACKUP_DIR, filename)
    default_config = _load(default_file)

    if not os.path.exists(backup_file):
        return default_config

    return default_config | _load(backup_file)


def backup_config(service_names: Iterable[str], filename: str) -> None:
    "Backup services to json file, if it's not already backed up."

    backup_file = os.path.join(config.BACKUP_DIR, filename)
    if os.path.exists(backup_file):
        backup_config = _load(backup_file)
        if backup_config and all(
            service_name in service_names for service_name in backup_config
        ):
            return  # if all has already been backed up
    else:
        backup_config = {}

    services_config: dict[str, list[str]] = {}
    for service_name in service_names:
        start_type = service.startup_type(service_name)
        if start_type == "disabled":
            continue    # skip disabled services
        start_value = service.startup_value(service_name)
        services_config[service_name] = [start_type, str(start_value)]

    configuration = backup_config | services_config
    if not configuration:
        return  # nothing to backup

    if not os.path.exists(config.BACKUP_DIR):
        os.mkdir(config.BACKUP_DIR)

    with open(backup_file, 'w') as file:
        file.write(json.dumps(configuration, indent=4))
