import httpx
import pytest
from pydantic import ValidationError

from aiopenapi3 import OpenAPI


def test_invalid_response(httpx_mock, petstore_expanded):
    httpx_mock.add_response(headers={"Content-Type": "application/json"}, json={"foo": 1})
    api = OpenAPI("test.yaml", petstore_expanded, session_factory=httpx.Client)

    with pytest.raises(ValidationError, match="2 validation errors for Pet") as r:
        p = api._.find_pet_by_id(data={}, parameters={"id": 1})
