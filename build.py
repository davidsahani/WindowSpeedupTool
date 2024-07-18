import os
import shutil
import subprocess
from typing import Any

import toml

from source.utils import config


def read_config(file_path: str) -> dict[str, Any]:
    with open(file_path) as file:
        data = toml.load(file)
    return data


def clean_dir(directory: str) -> None:
    try:
        shutil.rmtree(directory)
    except OSError:  # may fail once.
        shutil.rmtree(directory)


def copy_files(src_dir: str, dest_dir: str, *files: str) -> None:
    for file in files:
        shutil.copy2(os.path.join(src_dir, file), dest_dir)


def copy_dirs(src_dir: str, dest_dir: str, *dirs: str) -> None:
    for dir in dirs:
        shutil.copytree(
            os.path.join(src_dir, dir),
            os.path.join(dest_dir, dir)
        )


def build(name: str, src_dir: str, out_dir: str) -> int:
    styles_dir = os.path.join(src_dir, 'styles')
    icons_dir = os.path.join(src_dir, 'icons')
    icon_file = os.path.join(icons_dir, 'thunder-bolt.ico')

    pyinstaller_cmd = [
        "pyinstaller",
        "--distpath", out_dir,
        "--workpath", f"{out_dir}{os.sep}dist",
        "--specpath", f"{out_dir}{os.sep}dist",
        "--noconfirm", "--clean",
        "--contents-directory", "runtime",

        "--onedir", "--windowed", "--uac-admin",
        "--name", name,
        "--icon", icon_file,
        "--add-data", f"{icons_dir};icons/",
        "--add-data", f"{styles_dir};styles/",
        os.path.join(src_dir, "main.py")
    ]

    return subprocess.call(pyinstaller_cmd)


def main() -> None:
    script_dir = os.path.dirname(__file__)  # project directory.
    project_config = read_config(os.path.join(script_dir, "pyproject.toml"))

    project_name: str = project_config['project']['name']
    source_dir = os.path.join(script_dir, "source")
    output_dir = os.path.join(script_dir, "build")

    if os.path.exists(output_dir):
        clean_dir(output_dir)

    os.chdir(script_dir)  # change cwd to script directory.

    status = build(project_name, source_dir, output_dir)

    if status != 0:
        return  # abort build failed.

    output_dir = os.path.join(output_dir, project_name)

    # copy files to project output build directory.
    copy_files(
        script_dir, output_dir,
        "LICENSE", "INSTALL-DRIVERS.bat", config.CONFIG_FILE,
    )

    # copy directories to project output build directory.
    copy_dirs(script_dir, output_dir, config.load().config_dir, "bin")


if __name__ == '__main__':
    main()
