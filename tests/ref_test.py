"""
This file tests that $ref resolution works as expected, and that
allOfs are populated as expected as well.
"""
import pytest

from openapi3 import OpenAPI
from openapi3.schemas import Schema


def test_ref_resolution(petstore_expanded_spec):
    """
    Tests that $refs are resolved as we expect them to be
    """
    ref = petstore_expanded_spec.paths["/pets"].get.responses["default"].content["application/json"].schema

    assert type(ref) == Schema
    assert ref.type == "object"
    assert len(ref.properties) == 2
    assert "code" in ref.properties
    assert "message" in ref.properties
    assert ref.required == ["code", "message"]

    code = ref.properties["code"]
    assert code.type == "integer"
    assert code.format == "int32"

    message = ref.properties["message"]
    assert message.type == "string"


def test_allOf_resolution(petstore_expanded_spec):
    """
    Tests that allOfs are resolved correctly
    """
    ref = petstore_expanded_spec.paths["/pets"].get.responses["200"].content["application/json"].schema
    ref = petstore_expanded_spec.paths["/pets"].get.responses["200"].content["application/json"].schema

    assert type(ref) == Schema
    assert ref.type == "array"
    assert ref.items is not None

    items = ref.items
    assert type(items) == Schema
    assert sorted(items.required) == sorted(["id", "name"])
    assert len(items.properties) == 3
    assert "id" in items.properties
    assert "name" in items.properties
    assert "tag" in items.properties

    id_prop = items.properties["id"]
    id_prop = items.properties["id"]
    assert id_prop.type == "integer"
    assert id_prop.format == "int64"

    name = items.properties["name"]
    name = items.properties["name"]
    assert name.type == "string"

    tag = items.properties["tag"]
    assert tag.type == "string"


def test_resolving_nested_allof_ref(with_nested_allof_ref):
    """
    Tests that a schema with a $ref nested within a schema defined in an allOf
    parses correctly
    """
    spec = OpenAPI(with_nested_allof_ref)

    schema = spec.paths['/example'].get.responses['200'].content['application/json'].schema
    assert type(schema.properties['other']) == Schema
    assert schema.properties['other'].type == 'string'

    assert type(schema.properties['data'].items) == Schema
    assert 'bar' in schema.properties['data'].items.properties


def test_ref_allof_handling(with_ref_allof):
    """
    Tests that allOfs do not modify the originally loaded value of a $ref they
    includes (which would cause all references to that schema to be modified)
    """
    spec = OpenAPI(with_ref_allof)
    referenced_schema = spec.components.schemas['Example']

    # this should have only one property; the allOf from
    # paths['/allof-example']get.responses['200'].content['application/json'].schema
    # should not modify the component
    assert len(referenced_schema.properties) == 1, \
           "Unexpectedly found {} properties on components.schemas['Example']: {}".format(
                   len(referenced_schema.properties),
                   ", ".join(referenced_schema.properties.keys()),
            )

def test_ref_6901_refs(rfc_6901):
    """
    Tests that RFC 6901 escape codes, such as ~0 and ~1, are pared correctly
    """
    spec = OpenAPI(rfc_6901, validate=True)
    assert len(spec.errors()) == 0, spec.errors()

    # spec parsed, make sure our refs got the right values
    path = spec.paths['/ref-test']
    response = path.get.responses['200'].content['application/json'].schema

    assert response.properties['one'].type == 'string'
    assert response.properties['two'].type == 'int'
    assert response.properties['three'].type == 'array'

    # ensure the integer path components parsed as expected too
    assert response.properties['four'].type == 'string'
    assert response.properties['four'].example == 'it worked'

    # ensure integer path parsing does work as expected
    assert len(path.parameters) == 1
    assert path.parameters[0].name == 'example2'
