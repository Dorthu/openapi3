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
    with pytest.raises(SpecError, match=r"Expected .info to be of type Info, with required fields \['title', 'version'\]" ):
        spec = OpenAPI(broken)


def test_parsing_broken_refernece(broken_reference):
    """
    Tests that parsing fails correctly when a reference is broken
    """
    with pytest.raises(ReferenceResolutionError):
        spec = OpenAPI(broken_reference)


def test_parsing_wrong_parameter_name(has_bad_parameter_name):
    """
    Tests that parsing fails if parameter name for path parameters aren't
    actually in the path.
    """
    with pytest.raises(SpecError, match="Parameter name not found in path: different"):
        spec = OpenAPI(has_bad_parameter_name)


def test_parsing_dupe_operation_id(dupe_op_id):
    """
    Tests that duplicate operation Ids are an error
    """
    with pytest.raises(SpecError, match="Duplicate operationId dupe"):
        spec = OpenAPI(dupe_op_id)
