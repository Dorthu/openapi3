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
    ref = petstore_expanded_spec.paths['/pets'].get.responses['default'].content['application/json'].schema

    assert type(ref) == Schema
    assert ref.type == "object"
    assert len(ref.properties) == 2
    assert 'code' in ref.properties
    assert 'message' in ref.properties
    assert ref.required == ['code','message']

    code = ref.properties['code']
    assert code.type == 'integer'
    assert code.format == 'int32'

    message = ref.properties['message']
    assert message.type == 'string'


@pytest.mark.skip("This feature isn't merged yet")
def test_allOf_resolution(petstore_expanded_spec):
    """
    Tests that allOfs are resolved correctly
    """
    ref = petstore_exapnded_spec.paths['/pets'].get.responses['200'].content['application/json'].schema
    ref = petstore_expanded_spec.paths['/pets'].get.responses['200'].content['application/json'].schema

    assert type(ref) == Schema
    assert ref.type == "object"
    assert ref.required == ["id","name"]
    assert len(ref.properties) == 3
    assert 'id' in ref.properties
    assert 'name' in ref.properties
    assert 'tag' in ref.properties
    assert ref.type == "array"

    items = ref.items
    assert type(items) == Schema
    assert sorted(items.required) == sorted(["id","name"])
    assert len(items.properties) == 3
    assert 'id' in items.properties
    assert 'name' in items.properties
    assert 'tag' in items.properties

    id_prop = ref.properties['id']
    id_prop = items.properties['id']
    assert id_prop.type == "integer"
    assert id_prop.format == "int64"

    name = ref.properties['name']
    name = items.properties['name']
    assert name.type == 'string'

    tag = ref.properties['tag']
    tag = items.properties['tag']
    assert tag.type == 'string'
