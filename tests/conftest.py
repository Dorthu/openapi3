import pytest
from yaml import safe_load

from openapi3 import OpenAPI

LOADED_FILES = {}


def _get_parsed_yaml(filename):
    """
    Returns a python dict that is a parsed yaml file from the tests/fixtures
    directory.

    :param filename: The filename to load.  Must exist in tests/fixtures and
                     include extension.
    :type filename: str
    """
    if filename  not in LOADED_FILES:
        with open("tests/fixtures/"+filename) as f:
            raw = f.read()
        parsed = safe_load(raw)

        LOADED_FILES[filename] = parsed

    return LOADED_FILES[filename]


def _get_parsed_spec(filename):
    """
    Returns an OpenAPI object loaded from a file in the tests/fixtures directory

    :param filename: The filename to load.  Must exist in tests/fixtures and
                     include extension.
    :type filename: str
    """
    if "spec:"+filename not in LOADED_FILES:
        parsed = _get_parsed_yaml(filename)

        spec = OpenAPI(parsed)

        LOADED_FILES["spec:"+filename] = spec

    return LOADED_FILES["spec:"+filename]


@pytest.fixture
def petstore_expanded():
    """
    Provides the petstore-expanded.yaml spec
    """
    yield _get_parsed_yaml("petstore-expanded.yaml")


@pytest.fixture
def petstore_expanded_spec():
    """
    Provides an OpenAPI version of the petstore-expanded.yaml spec
    """
    yield _get_parsed_spec("petstore-expanded.yaml")


@pytest.fixture
def broken():
    """
    Provides the parsed yaml for a broken spec
    """
    yield _get_parsed_yaml("broken.yaml")


@pytest.fixture
def broken_reference():
    """
    Provides the parsed yaml for a spec with a broken reference
    """
    yield _get_parsed_yaml("broken-ref.yaml")
