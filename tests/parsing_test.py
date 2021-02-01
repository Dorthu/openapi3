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


def test_parsing_float_validation(float_validation_expanded):
    """
    Tests that `minimum` and similar validators work with floats.
    """
    spec = OpenAPI(float_validation_expanded)
    properties = spec.paths['/foo'].get.responses['200'].content['application/json'].schema.properties

    assert isinstance(properties['integer'].minimum, int)
    assert isinstance(properties['integer'].maximum, int)
    assert isinstance(properties['real'].minimum, float)
    assert isinstance(properties['real'].maximum, float)
