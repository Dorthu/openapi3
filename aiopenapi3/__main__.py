import sys
import sys

if sys.version_info >= (3, 9):
    from pathlib import Path
else:
    from pathlib3x import Path

from .openapi import OpenAPI

from .loader import FileSystemLoader


def main():
    name = sys.argv[1]

    try:
        OpenAPI.load_file(name, Path(name), loader=FileSystemLoader(Path().cwd()))
    except ValueError as e:
        print(e)
    else:
        print("OK")


if __name__ == "__main__":
    main()
