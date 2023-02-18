import json
import os
from typing import Iterable

from .service import display_name, startup_type, startup_value

DEFAULT_DIR = ".\\config"
BACKUP_DIR = ".\\backup_config"

LAPTOP_SERVICES = "laptop_services.json"
NORMAL_SERVICES = "normal_services.json"
NORMAL_SPECIFIC = "normal_specific_services.json"
ADVANCE_SERVICES = "advance_services.json"
UNSTOPPABLE_SERVICES = "unstoppable_services.json"
HIDDEN_SERVICES = "hidden_services.json"
NECESSARY_SERVICES = "necessary_services.json"
EXTRA_SERVICES = "extra_services.json"

SECURITY_SERVICES = "security_services.json"
NETWORK_SERVICES = "network_services.json"
ADVANCEX_SERVICES = "advancex_services.json"
WLAN_SERVICES = "wlan_services.json"


def _load(filepath: str) -> dict[str, list[str]]:
    "Load service configuration from a JSON file."

    with open(filepath) as file:
        services_config = json.load(file)
    return services_config


def load(filename: str) -> dict[str, str]:
    """Load service configuration from a JSON file.

    Return:
        merge of default and backup config if backup file exists.
    """
    backup_file = os.path.join(BACKUP_DIR, filename)
    default_file = os.path.join(DEFAULT_DIR, filename)
    default_config = {name: svc[0]
                      for name, svc in _load(default_file).items()}

    if not os.path.exists(backup_file):
        return default_config

    return default_config | \
        {name: svc[0] for name, svc in _load(backup_file).items()}


def backup(service_names: Iterable[str], filename: str) -> None:
    "Backup services to json file, if it's not already backed up."

    backup_file = os.path.join(BACKUP_DIR, filename)
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
        start_type = startup_type(service_name)
        if start_type == 'disabled':
            continue    # skip disabled services
        services_config[service_name] = [
            start_type, display_name(service_name)]

    configuration = backup_config | services_config
    if not configuration:
        return  # if empty, nothing to backup

    if not os.path.exists(BACKUP_DIR):
        os.mkdir(BACKUP_DIR)

    with open(backup_file, 'w') as file:
        file.write(json.dumps(configuration, indent=4))


def backup_reg(service_names: Iterable[str], filename: str) -> None:
    "Backup services to json file, if it's not already backed up."

    backup_file = os.path.join(BACKUP_DIR, filename)
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
        start_value = startup_value(service_name)
        if start_value == 4:
            continue    # skip disabled services
        services_config[service_name] = [
            str(start_value), display_name(service_name)]

    configuration = backup_config | services_config
    if not configuration:
        return  # if empty, nothing to backup

    if not os.path.exists(BACKUP_DIR):
        os.mkdir(BACKUP_DIR)

    with open(backup_file, 'w') as file:
        file.write(json.dumps(configuration, indent=4))
