import os
import re
import sys

PYTHON_DIR = os.path.dirname(sys.executable)
QTCORE_PYI_FILE = f"{PYTHON_DIR}\\Lib\\site-packages\\PyQt6\\QtCore.pyi"


def perform_patch(file_path: str) -> None:
    with open(file_path, "r") as file:
        lines = file.readlines()

    pattern = r"typing\.Callable\[\.\.\., Any\]"
    replacement = r"typing.Callable[..., typing.Any]"

    for i, line in enumerate(lines):
        if re.search(pattern, line):
            lines[i] = re.sub(pattern, replacement, line)
            print(f"Replaced line {i + 1}: {line.strip()}")
            break

    with open(file_path, 'w') as file:
        file.writelines(lines)


if __name__ == "__main__":
    perform_patch(QTCORE_PYI_FILE)
