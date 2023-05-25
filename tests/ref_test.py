"""
This file tests that $ref resolution works as expected, and that
allOfs are populated as expected as well.
"""
import pytest

from openapi3 import OpenAPI
from openapi3.object_base import ReferenceProxy
from openapi3.schemas import Schema
from openapi3.general import Reference


def test_ref_resolution(petstore_expanded_spec):
    """
    Tests that $refs are resolved as we expect them to be
    """
    ref = petstore_expanded_spec.paths["/pets"].get.responses["default"].content["application/json"].schema

    assert type(ref) == ReferenceProxy
    assert type(ref._proxy) == Schema
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

    assert type(ref) == Schema
    assert ref.type == "array"
    assert ref.items is not None

    items = ref.items
    assert type(items) == ReferenceProxy
    assert type(items._proxy) == Schema
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


def test_openapi_3_1_0_references(with_openapi_310_references):
    """
    Tests that expanded references, as defined in OpenAPI 3.1.0, work as described
    """
    # spec parses with expanded reference objects
    spec = OpenAPI(with_openapi_310_references)

    # the extended reference to Example did nothing
    example_ref = spec.components.pathItems["example"].get.responses["200"].content["application/json"]
    assert not hasattr(example_ref, "summary")
    assert not hasattr(example_ref, "description")

    # the original definition of the example Path is unchanged
    original_path = spec.components.pathItems["example"]
    assert original_path.summary == "/example"
    assert original_path.description == "/example"

    # the plain reference sees the original object's values
    normal_ref = spec.paths["/example"]
    assert normal_ref.summary == "/example"
    assert normal_ref.description == "/example"
    assert normal_ref == original_path
    assert normal_ref._proxy == original_path
    assert isinstance(normal_ref._original_ref, Reference)

    # the extended reference sees the new values
    extended_ref = spec.paths["/other"]
    assert extended_ref.summary == "/other"
    assert extended_ref.description == "/other"
    assert extended_ref == original_path
    assert extended_ref._proxy == original_path
    assert isinstance(extended_ref._original_ref, Reference)
    assert extended_ref._original_ref != normal_ref._original_ref


def test_reference_referencing_reference(with_reference_referencing_reference):
    spec = OpenAPI(with_reference_referencing_reference)

    assert type(spec.components.schemas["Example"].properties["real"]) == Schema, "Real property was not a schema?"
    assert type(spec.components.schemas["Example"].properties["reference"]) == Schema, "Reference property was not resolved"
    assert type(spec.paths["/test"].post.requestBody.content["application/json"].schema.properties["example"]) == Schema, "Reference reference was not resolved"
