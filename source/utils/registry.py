import typing
import winreg

if typing.TYPE_CHECKING:
    _KeyType = winreg._KeyType  # type: ignore


KEY_NAMES = {
    winreg.HKEY_CLASSES_ROOT: 'HKEY_CLASSES_ROOT',
    winreg.HKEY_CURRENT_USER: 'HKEY_CURRENT_USER',
    winreg.HKEY_LOCAL_MACHINE: 'HKEY_LOCAL_MACHINE',
    winreg.HKEY_USERS: 'HKEY_USERS',
    winreg.HKEY_PERFORMANCE_DATA: 'HKEY_PERFORMANCE_DATA',
    winreg.HKEY_CURRENT_CONFIG: 'HKEY_CURRENT_CONFIG',
    winreg.HKEY_DYN_DATA: 'HKEY_DYN_DATA',
}


class KeyNotExistsError(FileNotFoundError):
    """Raised when a key doesn't exist."""

    def __init__(self, key_path: str):
        super().__init__(f"{key_path} doesn't exist.")


def OpenKey(key: '_KeyType', sub_key: str, reserved: int = 0, access: int = 131097) -> winreg.HKEYType:
    """Opens the specified key.

    key
        An already open key, or any one of the predefined HKEY_* constants.
    sub_key
        A string that identifies the sub_key to open.
    reserved
        A reserved integer that must be zero. Default is zero.
    access
        An integer that specifies an access mask that describes the desired security access for the key. Default is KEY_READ.

    The result is a new handle to the specified key. If the function fails, an OSError exception is raised.
    """
    try:
        return winreg.OpenKey(key, sub_key, reserved, access)

    except FileNotFoundError:
        raise KeyNotExistsError(
            f"{KEY_NAMES[int(key)]}\\{sub_key}") from None

    except OSError as error:
        reg_path = f"{KEY_NAMES[int(key)]}\\{sub_key}"
        error.add_note(f"Couldn't open key: {reg_path}")
        raise error


def key_value(key: '_KeyType', sub_key: str, name: str) -> typing.Any:
    """Retrieve value of the specified sub-key from the Windows registry.

    Args:
        - key: An already open key, or any one of the predefined HKEY_* constants.
        - sub_key: A string that identifies the sub_key to open.
        - name: A string indicating the value to query.

    Return:
        Value of the specified sub-key.
    """
    reg_key = OpenKey(key, sub_key)

    try:
        return winreg.QueryValueEx(reg_key, name)[0]

    except FileNotFoundError:
        key_name = KEY_NAMES[int(key)]
        reg_path = f"{key_name}\\{sub_key}\\{name}"
        raise KeyNotExistsError(reg_path) from None

    except PermissionError as error:
        key_name = KEY_NAMES[int(key)]
        reg_path = f"{key_name}\\{sub_key}\\{name}"
        error.add_note(f"Couldn't read key: {reg_path}")
        raise error

    finally:
        winreg.CloseKey(reg_key)


def set_key_value(key: '_KeyType', sub_key: str, name: str, value: int) -> None:
    """Change the given key value in windows registry.

    Args:
        - key: An already open key, or any one of the predefined HKEY_* constants.
        - sub_key: A string that identifies the sub_key to open.
        - name: A string containing the name of the value to set.
        - value: A string that specifies the new value.
    """
    reg_key = OpenKey(key, sub_key, 0, winreg.KEY_SET_VALUE)

    try:
        winreg.SetValueEx(reg_key, name, 0, winreg.REG_DWORD, value)

    except OSError as error:
        path = f"{KEY_NAMES[int(key)]}\\{sub_key}"
        error.add_note(f"Couldn't write key: {path}")
        raise error

    finally:
        winreg.CloseKey(reg_key)


def create_key(key: '_KeyType', sub_key: str, name: str) -> None:
    """Create a new key in the Windows registry.

    Args:
        - key: An already open key, or any one of the predefined HKEY_* constants.
        - sub_key: A string that identifies the sub_key to open.
        - name: The name of the key this function opens or creates.
    """
    reg_key = OpenKey(key, sub_key, 0, winreg.KEY_ALL_ACCESS)

    try:
        new_key = winreg.CreateKeyEx(
            reg_key, name, 0,
            winreg.KEY_ALL_ACCESS
        )
        winreg.CloseKey(new_key)

    except OSError as error:
        path = f"{KEY_NAMES[int(key)]}\\{sub_key}"
        error.add_note(f"Couldn't create key: {path}")
        raise error

    finally:
        winreg.CloseKey(reg_key)


def del_key(key: '_KeyType', sub_key: str, name: str) -> None:
    """Delete the given key in the Windows registry.

    Args:
        - key: An already open key, or any one of the predefined HKEY_* constants.
        - sub_key: A string that identifies the sub_key to open.
        - name: The name of a subkey of the key identified by the key parameter. The key may not have subkeys.

    If the function succeeds, the entire key, including all of its values, is removed. If the function fails, an OSError exception is raised.
    """
    reg_key = OpenKey(key, sub_key, access=winreg.KEY_ALL_ACCESS)

    try:
        winreg.DeleteKey(reg_key, name)

    except OSError as error:
        path = f"{KEY_NAMES[int(key)]}\\{sub_key}"
        error.add_note(f"Couldn't delete key: {path}")
        raise error

    finally:
        winreg.CloseKey(reg_key)
