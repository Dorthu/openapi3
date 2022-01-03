import sys
import yaml
from pathlib import Path

from .openapi import OpenAPI

from .loader import FileSystemLoader


def main():
    name = sys.argv[1]
    loader = FileSystemLoader(Path().cwd())
    spec = loader.load(name)
    try:
        OpenAPI(name, spec, loader=loader)
    except ValueError as e:
        print(e)
    else:
        print("OK")


if __name__ == "__main__":
    main()
