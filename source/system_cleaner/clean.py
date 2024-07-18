import os
import shutil
import subprocess
from typing import Generator

from utils.threads import PROCESS_STARTUP_INFO

JUNK_EXTENSIONS = ['.tmp', '.chk', '.gid', '.log', '._mp', '.old']


def scan_dir(directory: str, extensions: list[str]) -> Generator[str, None, None]:
    "Scan the directory for files with specified file extensions."

    for dirpath, _dirnames, filenames in os.walk(directory):
        for filename in filenames:
            _root, ext = os.path.splitext(filename)
            if ext not in extensions:
                continue  # skip file
            yield os.path.join(dirpath, filename)


def clean_files(directory: str, extensions: list[str]) -> Generator[str, None, None]:
    "Delete files with specified file extensions from the provided directory."

    for file in scan_dir(directory, extensions):
        try:
            os.remove(file)
        except OSError as error:
            yield f"{error.__class__.__name__}: {error}"
        else:
            yield f"Deleted file: {file}"


def clean_dir(directory: str) -> Generator[str, None, None]:
    "Delete all the files in the specified directory."

    try:
        shutil.rmtree(directory)
    except OSError as error:
        yield f"{error.__class__.__name__}: {error}"
    else:
        yield f"Removed dir: {directory}"
        return

    try:
        filenames = os.listdir(directory)
    except OSError as error:
        yield f"{error.__class__.__name__}: {error}"
        return

    for filename in filenames:
        path = os.path.join(directory, filename)

        if os.path.isfile(path):
            try:
                os.remove(path)
            except OSError as error:
                yield f"{error.__class__.__name__}: {error}"
            else:
                yield f"Deleted file: {path}"
        else:
            try:
                shutil.rmtree(path)
            except OSError as error:
                yield f"{error.__class__.__name__}: {error}"
            else:
                yield f"Removed dir: {path}"


def clean_junkfiles() -> Generator[str, None, None]:
    "Clean the system junk files."

    # clean windows temp directory
    temp_dir = os.environ['TEMP']
    yield from clean_dir(temp_dir)
    # clean windows prefetch directory
    prefetch_dir = f"{os.environ['WINDIR']}\\Prefetch"
    yield from clean_dir(prefetch_dir)
    # clean all junks files from system drive
    system_dir = os.environ['SYSTEMDRIVE']
    yield from clean_files(system_dir, JUNK_EXTENSIONS)
    # clean '.bak' from windows directory
    windir = os.environ['WINDIR']
    yield from clean_files(windir, ['.bak'])


def clean_eventlogs() -> Generator[str, None, None]:
    "Clean windows event logs."

    proc = subprocess.Popen(
        ["wevtutil", "enum-logs"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        startupinfo=PROCESS_STARTUP_INFO
    )
    stdout, stderr = proc.communicate()

    if proc.returncode != 0:
        yield "Failed to list event logs."
        return

    if not stdout:
        yield "No event logs found."
        return

    for event_log in stdout.decode().splitlines():
        process = subprocess.Popen(
            ["wevtutil", "clear-log", event_log.strip()],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=PROCESS_STARTUP_INFO
        )
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            yield f"Cleared event log: {event_log}"
            continue    # continue on success

        error = (stderr or stdout or b'')
        if error:
            yield f"EventLogError: {error.decode().strip()}"
        else:
            yield f"Failed to clear event log: {event_log}"


def clean_windows_updates() -> Generator[str, None, None]:
    "Clean Windows update files."

    yield from clean_dir("C:\\Windows\\SoftwareDistribution")
    yield from clean_dir("C:\\ProgramData\\USOPrivate\\UpdateStore")
