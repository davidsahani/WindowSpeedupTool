from collections import defaultdict
from configparser import ConfigParser, Error
from dataclasses import dataclass
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
    Services: ServicesConfigType
    AdvancedServices: ServicesConfigType
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

        services_list: ServicesConfigType = []
        advanced_list: ServicesConfigType = []

        cls._process_sections(config, services_sections, services_list)
        cls._process_sections(config, advanced_sections, advanced_list)

        return cls(
            config_dir=config_dir,
            backup_dir=backup_dir,
            update_filename=filename,
            Services=services_list,
            AdvancedServices=advanced_list
        )

    @classmethod
    def _process_sections(cls, config: ConfigParser, sections_dict: defaultdict[str, list[str]], config_list: ServicesConfigType) -> None:
        def process_section(section: str) -> ServiceConfig | ServicesConfig | None:
            if section.endswith("Service"):
                service = dict(config[section])
                cls._validate_service_section(section, service)

                buttons = service.get("buttons")
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
                                section, service,
                                f"Invalid button: {button!r}, specified in configuration."  # noqa
                            )

                return ServiceConfig(
                    service_name=service["service_name"],
                    display_name=service["display_name"],
                    startup_type=service["startup_type"],
                    buttons=button_enums,
                )

            elif section.endswith("Services"):
                services = dict(config[section])
                cls._validate_services_section(section, services)

                extra_buttons = services.get("extra-buttons")
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
                                section, services,
                                f"Invalid extra button: {extra_button!r}, specified in configuration."  # noqa
                            )

                return ServicesConfig(
                    title=services["title"],
                    filename=services["filename"],
                    extra_buttons=buttons_enums
                )

        for sections in sections_dict.values():
            if len(sections) == 1:
                svc_config = process_section(sections[0])
                if svc_config is not None:
                    config_list.append(svc_config)

                continue  # after processing section.

            svc_configs = [svc_config for section in sections if (
                svc_config := process_section(section))]

            if svc_configs:
                config_list.append(svc_configs)

    @classmethod
    def _validate_service_section(cls, section: str, section_dict: dict[str, str]) -> None:
        for key in ("service_name", "display_name", "startup_type"):
            if key in section_dict:
                continue
            raise cls._configError(
                section, section_dict,
                f"{key!r} is not specified in the configuration."
            )

    @classmethod
    def _validate_services_section(cls, section: str, section_dict: dict[str, str]) -> None:
        for key in ("title", "filename"):
            if key in section_dict:
                continue
            raise cls._configError(
                section, section_dict,
                f"{key!r} is not specified in the configuration."
            )

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
