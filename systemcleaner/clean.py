import os
import shutil
import subprocess
from typing import Generator

from utils.power import PROCESS_STARTUP_INFO

JUNK_EXTENSIONS = ['.tmp', '.chk', '.gid', '.log', '._mp', '.old']


def scan_dir(directory: str, extensions: list[str]) -> Generator[str, None, None]:
    "Scan the directory for files with specified file extensions."

    if not directory.endswith('\\'):
        directory += '\\'

    for root, _, files in os.walk(directory):
        for file in files:
            _, ext = os.path.splitext(file)
            if ext not in extensions:
                continue  # skip file
            yield os.path.join(root, file)


def clear_files(directory: str, extensions: list[str]) -> Generator[str, None, None]:
    "Delete files with specified file extensions from the provided directory."

    for file in scan_dir(directory, extensions):
        try:
            os.remove(file)
        except FileNotFoundError:
            yield f"Invalid File, it doesn't exist: {file}"
        except PermissionError:
            yield f"No Permission to delete file: {file}"
        except OSError:
            yield f"Failed to delete file: {file}"
        else:
            yield f"Deleted file: {file}"


def clear_dir(directory: str) -> Generator[str, None, None]:
    "Delete all the files in the specified directory."

    for filename in os.listdir(directory):
        file = os.path.join(directory, filename)

        if os.path.isfile(file):
            try:
                os.remove(file)
            except FileNotFoundError:
                yield f"Invalid File, it doesn't exist: {file}"
            except PermissionError:
                yield f"No Permission to delete file: {file}"
            except OSError:
                yield f"Failed to delete file: {file}"
            else:
                yield f"Deleted file: {file}"
            continue
        try:
            shutil.rmtree(file)
        except FileNotFoundError:
            yield f"Invalid directory, it doesn't exist: {file}"
        except PermissionError:
            yield f"No Permission to delete dir: {file}"
        except OSError:
            yield f"Failed to remove dir: {file}"
        else:
            yield f"Removed dir: {file}"


def clean_junkfiles() -> Generator[str, None, None]:
    "Clean the system junk files."

    # clean windows temp directory
    temp_dir = os.environ['TEMP']
    yield from clear_dir(temp_dir)
    # clean windows prefetch directory
    prefetch_dir = f"{os.environ['WINDIR']}\\Prefetch"
    yield from clear_dir(prefetch_dir)
    # clean all junks files from system drive
    system_dir = os.environ['SYSTEMDRIVE']
    yield from clear_files(system_dir, JUNK_EXTENSIONS)
    # clean '.bak' from windows directory
    windir = os.environ['WINDIR']
    yield from clear_files(windir, ['.bak'])


def clean_eventlogs() -> Generator[str, None, None]:
    "Clean windows event logs."

    cmd = ["wevtutil.exe", "el"]
    event_logs = subprocess.check_output(
        cmd, startupinfo=PROCESS_STARTUP_INFO
    ).decode().splitlines()

    for event_log in event_logs:
        cmd = ["wevtutil.exe", "cl", event_log.strip()]
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=PROCESS_STARTUP_INFO
        )
        if not proc.wait():
            yield f"Cleared event log: {event_log}"
            continue    # continue on success
        if proc.stderr:
            msg = proc.stderr.read().decode().strip()
            yield f"Error: {msg}"
        else:
            yield f"Failed to clear event log: {event_log}"


def clean_windows_updates() -> Generator[str, None, None]:
    "Clean Windows updates files."

    yield from clear_dir(r'C:\Windows\SoftwareDistribution')
    yield from clear_dir(r'C:\ProgramData\USOPrivate\UpdateStore')
