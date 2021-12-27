import pytest
from openapi3 import FileSystemLoader,OpenAPI
import pathlib


def pytest_generate_tests(metafunc):
    argnames, dir, filterfn = metafunc.cls.params[metafunc.function.__name__]
    dir = pathlib.Path(dir)
    metafunc.parametrize(
        argnames, [[dir, i.name] for i in filter(filterfn, dir.iterdir())]
    )


class TestParseData:
    # a map specifying multiple argument sets for a test method
    params = {
        "test_data": [("dir","file"),"tests/data", lambda x: x.is_file() and x.suffix in (".json",".yaml")],
        "test_data_open5gs": [("dir","file"), "tests/data/open5gs/",
                         lambda x: x.is_file() and x.suffix in (".json",".yaml") and x.name.split("_")[0] not in ("TS29520","TS29509","TS29544","TS29517")],
    }

    def test_data(self, dir, file):
        loader = FileSystemLoader(pathlib.Path(dir))
        data = loader.load(pathlib.Path(file).name)
        spec = OpenAPI(data, loader=loader)

    def test_data_open5gs(self, dir, file):
        loader = FileSystemLoader(pathlib.Path(dir))
        data = loader.load(pathlib.Path(file).name)
#        if "servers" in "data":
        spec = OpenAPI(data, loader=loader)

