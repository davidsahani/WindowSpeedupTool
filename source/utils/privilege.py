"""Windows privilege elevation script

Provides privilege elevation functions
to get admin privilege on windows
via UAC prompt using ctypes and vbs.
"""

import ctypes
import os
import subprocess
import sys

# To hide process console window
PROCESS_STARTUP_INFO = subprocess.STARTUPINFO()
PROCESS_STARTUP_INFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW


def is_admin() -> bool:
    "Check if the current user is an administrator."

    return ctypes.windll.shell32.IsUserAnAdmin() == 1


def is_administrator(command: str = 'dism') -> bool:
    """Check privilege using command execution exit code.

    NOTE: Command provided must require admin privilege.
    """
    return subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        startupinfo=PROCESS_STARTUP_INFO
    ).wait() == 0


def exec(executable: str, argument: str | None = None) -> int:
    "Elevate any executable using ctypes."

    arg = f'"{argument}"' if argument is not None else ""
    return ctypes.windll.shell32.ShellExecuteW(
        None, "runas", f'"{executable}"', arg, None, 1)


def execute(executable: str, argument: str | None = None) -> int:
    "Elevate any executable using vb script."

    run_script_name = 'RunGetPrivilege.vbs'
    esc_script_name = 'GetPrivilege.vbs'
    tmpdir = os.getenv('TEMP') or os.getcwd()
    run_script = os.path.join(tmpdir, run_script_name)
    esc_script = os.path.join(tmpdir, esc_script_name)
    # create elevation vb script to run executable.
    with open(esc_script, 'w') as escal_file:
        escal_file.write('Set UAC = CreateObject("Shell.Application")' + '\n')
        if argument is None:
            line = f'UAC.ShellExecute "{executable}", "", "", "runas", 1'
        else:
            line = f'UAC.ShellExecute "{executable}", """{argument}""", "", "runas", 1'  # noqa
        escal_file.write(line)
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
    status = subprocess.Popen(
        f'{wscript} "{run_script}"',
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        startupinfo=PROCESS_STARTUP_INFO
    ).wait()  # wait for process to finish.
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
    "Elevate python script using ctypes."

    pyexec = get_pyexec(pyfile)
    return exec(pyexec, pyfile)


def execute_pyscript(pyfile: str) -> int:
    "Elevate python script using vb script."

    pyexec = get_pyexec(pyfile)
    return execute(pyexec, pyfile)
