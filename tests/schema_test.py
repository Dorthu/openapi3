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