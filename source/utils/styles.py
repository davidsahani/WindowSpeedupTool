import os

parent_dir = os.path.dirname(os.path.dirname(__file__))
styles_dir = os.path.join(parent_dir, "styles")


def get(style_name: str) -> str:
    "Return the named style file contents."

    filepath = os.path.join(styles_dir, style_name + '.qss')
    try:
        with open(filepath) as file:
            return file.read()
    except FileNotFoundError:
        raise ValueError(
            f'{style_name!r} style not found in {styles_dir!r}') from None


if __name__ == '__main__':
    for style in os.listdir(styles_dir):
        print(style)
