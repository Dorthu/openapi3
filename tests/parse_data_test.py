import pytest
from aiopenapi3 import FileSystemLoader, OpenAPI
import pathlib

import yarl

URLBASE = yarl.URL("http://127.1.1.1/open5gs/")


def pytest_generate_tests(metafunc):
    argnames, dir, filterfn = metafunc.cls.params[metafunc.function.__name__]
    dir = pathlib.Path(dir).expanduser()
    metafunc.parametrize(
        argnames,
        [[dir, i.name] for i in sorted(filter(filterfn, dir.iterdir() if dir.exists() else []), key=lambda x: x.name)],
    )


class TestParseData:
    # a map specifying multiple argument sets for a test method
    params = {
        "test_data": [("dir", "file"), "tests/data", lambda x: x.is_file() and x.suffix in (".json", ".yaml")],
        "test_data_open5gs": [
            ("dir", "file"),
            "tests/data/open5gs/",
            lambda x: x.is_file()
            and x.suffix in (".json", ".yaml")
            and x.name.split("_")[0] not in ("TS29520", "TS29509", "TS29544", "TS29517"),
        ],
    }

    def test_data(self, dir, file):
        OpenAPI.load_file(str(URLBASE / file), pathlib.Path(file), loader=FileSystemLoader(pathlib.Path(dir)))

    def test_data_open5gs(self, dir, file):
        OpenAPI.load_file(str(URLBASE / file), pathlib.Path(file), loader=FileSystemLoader(pathlib.Path(dir)))
