import json
import os
from typing import Final, Iterable

from .config_parser import Config, Service
from .service import display_name, startup_type
from .styles import parent_dir

CONFIG_FILE: Final = "config.ini"
PROJECT_DIR: Final = os.path.dirname(parent_dir)


def abs_path(path: str) -> str:
    "Return absolute path relative to PROJECT_DIR if path is not absolute."

    return os.path.normpath(os.path.join(PROJECT_DIR, path)) \
        if not os.path.isabs(path) else path


def load() -> Config:
    """Load the main configuration object.

    Raise:
        FileNotFoundError: If config file is not found.
    """
    file = abs_path(CONFIG_FILE)
    if not os.path.exists(file):
        raise FileNotFoundError(f"File not found: {file!r}")
    return Config.from_file(file)


def read_file(filepath: str) -> dict[str, list[str]]:
    "Return services configuration from a JSON file."

    with open(filepath) as file:
        return json.load(file)


def load_file(filename: str, config_dir: str, backup_dir: str) -> list[Service]:
    """Load services configuration from a JSON file.

    Return:
        list[Service]: Services created from primary and backup configurations.

    Raise:
        FileNotFoundError: If the primary configuration file is not found.
    """
    config_file = os.path.join(abs_path(config_dir), filename)
    backup_file = os.path.join(abs_path(backup_dir), filename)

    if not os.path.exists(config_file):
        path = abs_path(config_dir)

        if os.path.exists(path):
            raise FileNotFoundError(
                f"There's no file {filename!r} in config_dir: {path}"
            )
        raise FileNotFoundError(f"config_dir: '{path}' doesn't exist.")

    configuration = read_file(config_file) | (
        read_file(backup_file) if os.path.exists(backup_file) else {})

    return [
        Service(service_name=name,
                startup_type=value[0],
                display_name=value[1])
        for name, value in configuration.items()
    ]


def backup(service_names: Iterable[str], backup_dir: str, filename: str) -> None:
    "Backup services to a JSON file if they are not already backed up."

    backup_dirpath = abs_path(backup_dir)
    backup_file = os.path.join(backup_dirpath, filename)

    backup_config = read_file(backup_file) \
        if os.path.exists(backup_file) else {}

    services_config: dict[str, list[str]] = {}

    for service_name in service_names:
        if service_name in backup_config:
            continue

        start_type = startup_type(service_name).value
        if start_type == 'disabled' or start_type is None:
            continue  # skip disabled services

        svc_display_name = display_name(service_name).value
        if svc_display_name is None:
            continue  # skip services with no retrievable display name

        services_config[service_name] = [start_type, svc_display_name]

    if not services_config:
        return  # nothing to backup.

    configuration = backup_config | services_config

    if not os.path.exists(backup_dirpath):
        os.mkdir(backup_dirpath)

    with open(backup_file, 'w') as file:
        file.write(json.dumps(configuration, indent=4))
