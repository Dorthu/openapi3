"""
This file tests that $ref resolution works as expected, and that
allOfs are populated as expected as well.
"""
import typing

import pytest


from openapi3 import OpenAPI
from openapi3.schemas import Schema

from pydantic.main import ModelMetaclass

def test_ref_resolution(petstore_expanded_spec):
    """
    Tests that $refs are resolved as we expect them to be
    """
    ref = petstore_expanded_spec.paths['/pets'].get.responses['default'].content['application/json'].schema_

    assert type(ref._target) == Schema
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


def test_allOf_resolution(petstore_expanded_spec):
    """
    Tests that allOfs are resolved correctly
    """
    ref = petstore_expanded_spec.paths['/pets'].get.responses['200'].content['application/json'].schema_.get_type()

    assert type(ref) == ModelMetaclass
    assert typing.get_origin(ref.__fields__["__root__"].outer_type_) == list

    items = typing.get_args(ref.__fields__["__root__"].outer_type_)[0].__fields__

    assert sorted(map(lambda x: x.name, filter(lambda y: y.required==True, items.values()))) == sorted(["id","name"])

    assert sorted(map(lambda x: x.name, items.values())) == ["id","name","tag"]

    assert items['id'].outer_type_ == int
    assert items['name'].outer_type_ == str
    assert items["tag"].outer_type_ == str
