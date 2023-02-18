import os

styles_dir = os.path.dirname(__file__)


def get(style_name: str) -> str:
    "Return the named style file contents."

    filepath = os.path.join(styles_dir, style_name + '.qss')
    try:
        with open(filepath) as file:
            return file.read()
    except FileNotFoundError:
        raise ValueError(
            f'{style_name!r} style not found in {styles_dir!r}') from None
