import winreg


def key_value(key_type: int, reg_path: str, key_name: str) -> int:
    """Retrieve value of a specified key in the Windows registry.

    Return:
        Key value

    Raise:
        ValueError: if key doesn't exist
        OSError: when key path can't be opened
        FileNotFoundError: if key can't be opened
    """
    reg_key = winreg.OpenKey(key_type, reg_path)
    try:
        value, _ = winreg.QueryValueEx(reg_key, key_name)
    except FileNotFoundError as error:
        raise ValueError(error.strerror)
    else:
        return value
    finally:
        winreg.CloseKey(reg_key)


def set_key_value(key_type: int, key_path: str, key_name: str, value: int) -> int:
    """Change the given key value

    Return:
        0 on success,
        1 on failure,
        2 if key doesn't exist

    Raise:
        OSError: when key path can't be opened
    """
    try:
        key = winreg.OpenKey(key_type, key_path, 0, winreg.KEY_SET_VALUE)
    except FileNotFoundError:
        return 2
    try:
        winreg.SetValueEx(key, key_name, 0, winreg.REG_DWORD, value)
    except OSError:
        return 1
    else:
        return 0
    finally:
        winreg.CloseKey(key)


def create_key(key_type: int, key_path: str, key_name: str) -> int:
    """Create a new key in the Windows registry.

    Return:
        0 on success,
        1 on failure,
        2 if key doesn't exist

    Raise:
        OSError: when key path can't be opened
    """
    try:
        key = winreg.OpenKey(key_type, key_path, 0, winreg.KEY_ALL_ACCESS)
    except FileNotFoundError:
        return 2
    try:
        new_key = winreg.CreateKeyEx(
            key, key_name, 0,
            winreg.KEY_ALL_ACCESS)
        winreg.CloseKey(new_key)
    except OSError:
        return 1
    else:
        return 0
    finally:
        winreg.CloseKey(key)


def del_key(key_type: int, key_path: str, key_name: str) -> int:
    """Delete the given key

    Return:
        0 on success,
        1 on failure,
        2 if key doesn't exist

    Raise:
        OSError: when key path can't be opened
    """
    try:
        key = winreg.OpenKey(key_type, key_path, access=winreg.KEY_ALL_ACCESS)
    except FileNotFoundError:
        return 2
    try:
        winreg.DeleteKey(key, key_name)
    except OSError:
        return 1
    else:
        return 0
    finally:
        winreg.CloseKey(key)
