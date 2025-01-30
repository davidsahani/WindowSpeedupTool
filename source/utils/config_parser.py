from collections import defaultdict
from configparser import ConfigParser, Error
from contextlib import suppress
from dataclasses import dataclass, fields
from enum import Enum
from typing import KeysView, override, Self, TypeAlias


class ConfigurationError(Error):
    def __init__(self, section: str, message: str) -> None:
        self.section = section
        self.message = message

    @override
    def __str__(self) -> str:
        cls_name = self.__class__.__name__
        return f"{cls_name}: {self.section}\n\n{self.message}\n"


class Button(Enum):
    START = "start"
    STOP = "stop"
    ENABLE = "enable"
    DISABLE = "disable"


class ExtraButton(Enum):
    STOP_RUNNING = "stop_running"
    DISABLE_RUNNING = "disable_running"


@dataclass
class Service:
    service_name: str
    display_name: str
    startup_type: str


@dataclass
class ServiceConfig:
    service_name: str
    display_name: str
    startup_type: str
    buttons: list[Button]


@dataclass
class ServicesConfig:
    title: str
    filename: str
    extra_buttons: list[ExtraButton]


ServicesConfigType: TypeAlias = list[
    ServiceConfig | ServicesConfig | list[ServiceConfig | ServicesConfig]
]


@dataclass
class Config:
    config_dir: str
    backup_dir: str
    update_filename: str
    windows_services: ServicesConfigType
    advance_services: ServicesConfigType
    _default_keys: KeysView[str] | None = None

    @classmethod
    def from_file(cls, filepath: str) -> Self:
        config = ConfigParser()  # Initialize parser.
        config.read(filepath)    # Read the INI file.
        cls._default_keys = config.defaults().keys()

        config_dir = config.get('DEFAULT', 'config_dir')
        backup_dir = config.get('DEFAULT', 'backup_dir')
        filename = config.get('DEFAULT', 'update_filename')

        services_sections: defaultdict[str, list[str]] = defaultdict(list)
        advanced_sections: defaultdict[str, list[str]] = defaultdict(list)

        for section in config.sections():
            if section.endswith(("Advanced.Service", "Advanced.Services")):
                section_prefix = section.split(".", maxsplit=1)[0]
                advanced_sections[section_prefix].append(section)
            elif section.endswith(("Service", "Services")):
                section_prefix = section.split(".", maxsplit=1)[0]
                services_sections[section_prefix].append(section)

        services_list = cls._process_sections(config, services_sections)
        advanced_list = cls._process_sections(config, advanced_sections)

        return cls(
            config_dir=config_dir,
            backup_dir=backup_dir,
            update_filename=filename,
            windows_services=services_list,
            advance_services=advanced_list
        )

    @classmethod
    def _process_sections(cls, config: ConfigParser, sections_dict: defaultdict[str, list[str]]) -> ServicesConfigType:
        service_field_names = [field.name for field in fields(ServiceConfig)]
        services_field_names = [field.name for field in fields(ServicesConfig)]
        with suppress(ValueError):  # remove not required field names
            service_field_names.remove("buttons")
            services_field_names.remove("extra_buttons")

        def process_section(section: str) -> ServiceConfig | ServicesConfig | None:
            if section.endswith("Service"):
                kwargs: dict[str, str] = {}
                field_items = dict(config[section])

                for field_name in service_field_names:
                    value = field_items.get(field_name)
                    if value is None:
                        raise cls._configError(
                            section, field_items,
                            f"{field_name!r} is not specified in the configuration."
                        )
                    kwargs[field_name] = value

                buttons = field_items.get("buttons")
                button_enums: list[Button] = []

                for button in buttons.split(",") if buttons else []:
                    button = button.strip()

                    match button.lower():
                        case Button.START.value:
                            button_enums.append(Button.START)
                        case Button.STOP.value:
                            button_enums.append(Button.STOP)
                        case Button.ENABLE.value:
                            button_enums.append(Button.ENABLE)
                        case Button.DISABLE.value:
                            button_enums.append(Button.DISABLE)
                        case _:
                            raise cls._configError(
                                section, field_items,
                                f"Invalid button: {button!r}, specified in configuration."  # noqa
                            )

                return ServiceConfig(**kwargs, buttons=button_enums)

            elif section.endswith("Services"):
                kwargs: dict[str, str] = {}
                field_items = dict(config[section])

                for field_name in services_field_names:
                    value = field_items.get(field_name)
                    if value is None:
                        raise cls._configError(
                            section, field_items,
                            f"{field_name!r} is not specified in the configuration."
                        )
                    kwargs[field_name] = value

                extra_buttons = field_items.get("extra-buttons")
                buttons_enums: list[ExtraButton] = []

                for extra_button in extra_buttons.split(",") if extra_buttons else []:
                    extra_button = extra_button.strip()

                    match extra_button.lower():
                        case ExtraButton.STOP_RUNNING.value:
                            buttons_enums.append(ExtraButton.STOP_RUNNING)
                        case ExtraButton.DISABLE_RUNNING.value:
                            buttons_enums.append(ExtraButton.DISABLE_RUNNING)
                        case _:
                            raise cls._configError(
                                section, field_items,
                                f"Invalid extra button: {extra_button!r}, specified in configuration."  # noqa
                            )

                return ServicesConfig(**kwargs, extra_buttons=buttons_enums)

        configs_list: ServicesConfigType = []

        for sections in sections_dict.values():
            svc_configs: list[ServiceConfig | ServicesConfig] = []

            for section in sections:
                svc_config = process_section(section)
                if svc_config is not None:
                    svc_configs.append(svc_config)

            if not svc_configs:
                continue
            if len(svc_configs) == 1:
                configs_list.append(svc_configs[0])
            else:
                configs_list.append(svc_configs)

        return configs_list

    @classmethod
    def _configError(cls, section: str, section_dict: dict[str, str], message: str) -> ConfigurationError:
        """Return ConfigurationError after filtering default section keys."""
        section_items = "\n".join([
            f"{key}={value}" for key, value in section_dict.items(
            ) if key not in (cls._default_keys or [])
        ])

        if not section_items:
            return ConfigurationError(section, message)

        error = f"[{section}]\n{section_items}\n\n{message}"
        return ConfigurationError(section, error)
