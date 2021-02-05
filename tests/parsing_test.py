"""
Tests parsing specs
"""
import pytest

from openapi3 import OpenAPI, SpecError, ReferenceResolutionError


def test_parse_from_yaml(petstore_expanded):
    """
    Tests that we can parse a valid yaml file
    """
    spec = OpenAPI(petstore_expanded)


def test_parsing_fails(broken):
    """
    Tests that broken specs fail to parse
    """
    with pytest.raises(SpecError):
        spec = OpenAPI(broken)


def test_parsing_broken_refernece(broken_reference):
    """
    Tests that parsing fails correctly when a reference is broken
    """
    with pytest.raises(ReferenceResolutionError):
        spec = OpenAPI(broken_reference)


def test_object_example(obj_example_expanded):
    """
    Tests that `example` exists.
    """
    spec = OpenAPI(obj_example_expanded)
    schema = spec.paths['/check-dict'].get.responses['200'].content['application/json'].schema
    assert isinstance(schema.example, dict)
    assert isinstance(schema.example['real'], float)

    schema = spec.paths['/check-str'].get.responses['200'].content['text/plain']
    assert isinstance(schema.example, str)
