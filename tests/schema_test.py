import pytest

from openapi3 import OpenAPI
from openapi3.errors import ModelError

from unittest.mock import patch, MagicMock


def test_invalid_response(petstore_expanded):
    api = OpenAPI(petstore_expanded)
    resp = MagicMock(status_code=200, headers={"Content-Type":"application/json"}, json=lambda: {'foo':1})
    with patch("requests.sessions.Session.send", return_value=resp) as s:
        with pytest.raises(ModelError, match="Schema Pet got unexpected attribute keys {'foo'}") as r:
            api.call_find_pet_by_id(data={}, parameters={"id":1})
            print(r)


def test_schema_without_properties(schema_without_properties):
    """
    Tests that a response model is generated, and responses parsed correctly, for
    response schemas without properties
    """
    api = OpenAPI(schema_without_properties)
    resp = MagicMock(
        status_code=200,
        headers={
            "Content-Type":"application/json"
        },
        json=lambda: {
            "example": "it worked",
            "no_properties": {},
        }
    )

    with patch("requests.sessions.Session.send", return_value=resp) as s:
        result = api.call_noProps()

    assert result.example == "it worked"

    # the schema without properties did get its own named type defined
    assert type(result.no_properties).__name__ == "no_properties"
    # and it has no slots
    assert len(type(result.no_properties).__slots__) == 0
