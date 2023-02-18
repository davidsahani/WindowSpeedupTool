"""Windows privilege elevation script

Provides privilege elevation functions
to get admin privilege on windows
via UAC prompt using ctypes and vbs.
"""

import ctypes
import os
import subprocess
import sys
from typing import NoReturn


def is_admin() -> bool:
    "Check if the current user is an administrator."

    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def is_administrator(command: str = 'dism') -> bool:
    "Check privilege using command execution exit code."

    pipe = subprocess.Popen(command, stdout=subprocess.DEVNULL)
    return not pipe.wait()


def exec(executable: str, argument: str = '') -> int:
    "Elevate any executable using ctypes."

    return ctypes.windll.shell32.ShellExecuteW(
        None, "runas", f'"{executable}"', f'"{argument}"', None, 1)


def execute(executable: str, argument: str = '') -> int:
    "Elevate any executable using vb script."

    run_script_name = 'Run_GetPrivilege.vbs'
    esc_script_name = 'GetPrivilege.vbs'
    tmpdir = os.getenv('TEMP') or os.getcwd()
    run_script = os.path.join(tmpdir, run_script_name)
    esc_script = os.path.join(tmpdir, esc_script_name)
    # create elevation vb script to run executable.
    with open(esc_script, 'w') as escal_file:
        escal_file.write('Set UAC = CreateObject("Shell.Application")' + '\n')
        escal_file.write(
            f'UAC.ShellExecute "{executable}", """{argument}""", "", "runas", 1'
        )
    # create vb script to run elevation vb script hidden.
    with open(run_script, 'w') as launch_file:
        launch_file.write(
            f'CreateObject("Wscript.Shell").Run "{esc_script}", 0, True')
    # get 'wscript.exe'
    comspec = os.getenv('COMSPEC') or 'C:\\Windows\\system32\\cmd.exe'
    system32 = os.path.dirname(comspec)
    wscript = os.path.join(system32, 'wscript.exe')
    if not os.path.exists(wscript):
        raise FileNotFoundError(f"'wscript.exe' not found in {system32!r}")
    # run wscript.exe to execute vb script without window.
    startup_info = subprocess.STARTUPINFO()  # to hide console
    startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    pipe = subprocess.Popen(f'{wscript} "{run_script}"',
                            stdout=subprocess.DEVNULL,
                            startupinfo=startup_info)
    status = pipe.wait()  # wait for process to finish.
    # delete files after execution.
    os.remove(run_script)
    os.remove(esc_script)
    return status


def get_pyexec(pyfile: str) -> str:
    "Return python executable based on pyfile."

    pyexec = sys.executable
    ext = os.path.splitext(pyfile)[-1].lower()
    if ext != '.pyw':
        return pyexec
    pypath = os.path.dirname(pyexec)
    pywexec = os.path.join(pypath, 'pythonw.exe')
    if not os.path.exists(pywexec):
        raise FileNotFoundError(f"'pythonw.exe' not found in {pypath!r}")
    return pywexec


def exec_pyscript(pyfile: str) -> int:
    "elevate python script using ctypes."

    pyexec = get_pyexec(pyfile)
    return exec(pyexec, pyfile)  # elevate python file.


def execute_pyscript(pyfile: str) -> int:
    "elevate python script using vb script."

    pyexec = get_pyexec(pyfile)
    return execute(pyexec, pyfile)  # elevate python file.


def runasadmin(file: str = '') -> None | NoReturn:
    """
    Check privilege and elevate the `.exe` or `.py`, `.pyw`
    files accordingly with admin privilege using ctypes.

    NOTE: script exits after elevation
    """

    if is_admin():
        return  # Return if already has privilege.

    if file.endswith(('.py', '.pyw')):
        status = exec_pyscript(file or sys.argv[0])  # elevate python file.
    else:
        status = exec(file or sys.argv[0])  # elevate python file.
    sys.exit(status)  # Exit the current script to prevent running below code.


def runasadministrator(file: str = '') -> None | NoReturn:
    """
    Check privilege and elevate the `.exe` or `.py`, `.pyw`
    files accordingly with admin privilege using vb script.

    NOTE: script exits after elevation
    """

    if is_administrator():
        return  # Return if already has privilege.

    if file.endswith(('.py', '.pyw')):
        status = execute_pyscript(file or sys.argv[0])  # elevate python file.
    else:
        status = execute(file or sys.argv[0])  # elevate python file.
    sys.exit(status)  # Exit the current script to prevent running below code.
