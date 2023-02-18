import ctypes

import psutil


def processes() -> list[tuple[int, str]]:
    "Return list of all the running processes."

    procs: list[tuple[int, str]] = []
    for process in psutil.process_iter():
        procs.append((process.pid, process.name()))
    return procs


def pid(process_name: str) -> int:
    "Return pid for the process name."

    for proc in psutil.process_iter():
        if proc.name() == process_name:
            return proc.pid
    raise psutil.NoSuchProcess("No such process with that name is running")


def kill(process_id: int) -> int:
    """Kill a process with the given process ID.

    Return:
        kill status for the given process ID
    """
    try:
        psutil.Process(process_id).kill()
    except psutil.NoSuchProcess:
        return 1
    except psutil.AccessDenied:
        return 2
    except psutil.Error:
        return 3
    else:
        return 0


def suspend(process_id: int) -> int | None:
    "Suspend the process with the given process ID."

    # Check if the process exists
    if not ctypes.windll.kernel32.GenerateConsoleCtrlEvent(0, process_id):
        raise psutil.NoSuchProcess(
            f"Process with ID {process_id} does not exist")

    # Check if the process is already suspended
    if ctypes.windll.kernel32.WaitForSingleObject(process_id, 0) != 0x00000102:
        return None  # when f"Process with ID {pid} is already suspended")

    # Suspend the process
    return ctypes.windll.kernel32.SuspendThread(process_id)


def resume(process_id: int) -> int | None:
    "Resume the process with the given process ID."

    # Check if the process exists
    if not ctypes.windll.kernel32.GenerateConsoleCtrlEvent(0, process_id):
        raise psutil.NoSuchProcess(
            f"Process with ID {process_id} does not exist")

    # Check if the process is already running
    if ctypes.windll.kernel32.WaitForSingleObject(process_id, 0) == 0:
        return None  # when f"Process with ID {pid} is not suspended")

    # Resume the process
    return ctypes.windll.kernel32.ResumeThread(process_id)
