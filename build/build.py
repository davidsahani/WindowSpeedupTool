import os
import shutil
import subprocess

PROJECT_NAME = "WindowSpeedupTool"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))
PROJECT_BUILD_DIR = os.path.join(SCRIPT_DIR, 'project')
PROJECT_OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'output')


def read_file(filepath: str) -> list[str]:
    with open(filepath, 'r') as file:
        return file.read().splitlines()


def copy_source_files() -> None:
    exclude = read_file(os.path.join(SCRIPT_DIR, '.exclude'))

    for dirpath, _, filenames in os.walk(PARENT_DIR):
        if dirpath == SCRIPT_DIR or dirpath.startswith(SCRIPT_DIR + os.path.sep):
            continue  # skip script's directory and its subdirectories

        if any(e in dirpath for e in exclude):
            continue  # skip directory

        for filename in filenames:
            if filename in exclude:
                continue  # skip file

            source_path = os.path.join(dirpath, filename)
            relative_path = os.path.relpath(source_path, PARENT_DIR)
            destination_path = os.path.join(PROJECT_BUILD_DIR, relative_path)
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            shutil.copy(source_path, destination_path)


def copy_include_files() -> None:
    include = read_file(os.path.join(SCRIPT_DIR, '.include'))
    destination_dir = os.path.join(PROJECT_OUTPUT_DIR, PROJECT_NAME)

    for dir_path in os.listdir(PARENT_DIR):
        if dir_path not in include:
            continue  # skip directory

        curr_path = os.path.join(PARENT_DIR, dir_path)

        if os.path.isfile(curr_path):
            shutil.copy(curr_path, destination_dir)
            continue

        for dirpath, _, filenames in os.walk(curr_path):
            if dirpath == SCRIPT_DIR or dirpath.startswith(SCRIPT_DIR + os.path.sep):
                continue  # skip script directory and it's subdirectories
            for filename in filenames:
                source_path = os.path.join(dirpath, filename)
                relative_path = os.path.relpath(source_path, PARENT_DIR)
                destination_path = os.path.join(destination_dir, relative_path)
                os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                shutil.copy(source_path, destination_path)


def build_project() -> int:
    icon_file = os.path.join(PROJECT_BUILD_DIR, 'icons', 'thunder-bolt.ico')
    icons_dir = os.path.join(PROJECT_BUILD_DIR, 'icons')
    config_dir = os.path.join(PROJECT_BUILD_DIR, 'config')
    styles_dir = os.path.join(PROJECT_BUILD_DIR, 'styles')
    install_drivers_file = os.path.join(
        PROJECT_BUILD_DIR, 'INSTALL-DRIVERS.bat')

    pyinstaller_cmd = [
        "pyinstaller",
        "--distpath", PROJECT_OUTPUT_DIR,
        "--noconfirm", "--clean",

        "--onedir", "--windowed", "--uac-admin",
        "--name", PROJECT_NAME,
        "--icon", icon_file,
        "--add-data", f"{icons_dir};icons/",
        "--add-data", f"{config_dir};config/",
        "--add-data", f"{styles_dir};styles/",
        "--add-data", f"{install_drivers_file};.",
        os.path.join(PROJECT_BUILD_DIR, "windowspeeduptool.py")
    ]

    return subprocess.call(pyinstaller_cmd)


def main() -> None:
    if os.path.exists(PROJECT_BUILD_DIR):
        shutil.rmtree(PROJECT_BUILD_DIR)

    # copy source files excluding .exclude file entries
    copy_source_files()

    # build the project
    os.chdir(PROJECT_BUILD_DIR)
    status = build_project()
    if status != 0:
        print("Pyinstaller failed to build the project")
        return  # return on failure, don't proceed with copying files

    # copy files mentioned in .include file
    copy_include_files()


if __name__ == '__main__':
    main()
