"""
This file tests that paths are parsed and populated correctly
"""
import base64
import uuid
import pathlib

import pytest
import httpx
import yarl

from aiopenapi3 import OpenAPI
from aiopenapi3.v30.schemas import Schema


URLBASE = "/"


def test_paths_exist(petstore_expanded_spec):
    """
    Tests that paths are parsed correctly
    """
    assert "/pets" in petstore_expanded_spec.paths._paths
    assert "/pets/{id}" in petstore_expanded_spec.paths._paths
    assert len(petstore_expanded_spec.paths._paths) == 2


def test_operations_exist(petstore_expanded_spec):
    """
    Tests that methods are populated as expected in paths
    """
    pets_path = petstore_expanded_spec.paths["/pets"]
    assert pets_path.get is not None
    assert pets_path.post is not None
    assert pets_path.put is None
    assert pets_path.delete is None

    pets_id_path = petstore_expanded_spec.paths["/pets/{id}"]
    assert pets_id_path.get is not None
    assert pets_id_path.post is None
    assert pets_id_path.put is None
    assert pets_id_path.delete is not None


def test_operation_populated(petstore_expanded_spec):
    """
    Tests that operations are populated as expected
    """
    op = petstore_expanded_spec.paths["/pets"].get

    # check description and metadata populated correctly
    assert op.operationId == "findPets"
    assert op.description.startswith("Returns all pets from the system")
    assert op.summary is None

    # check parameters populated correctly
    assert len(op.parameters) == 2

    param1 = op.parameters[0]
    assert param1.name == "tags"
    assert param1.in_ == "query"
    assert param1.description == "tags to filter by"
    assert param1.required == False
    assert param1.style == "form"
    assert param1.schema_ is not None
    assert param1.schema_.type == "array"
    assert param1.schema_.items.type == "string"

    param2 = op.parameters[1]
    assert param2.name == "limit"
    assert param2.in_ == "query"
    assert param2.description == "maximum number of results to return"
    assert param2.required == False
    assert param2.schema_ is not None
    assert param2.schema_.type == "integer"
    assert param2.schema_.format == "int32"

    # check that responses populated correctly
    assert "200" in op.responses
    assert "default" in op.responses
    assert len(op.responses) == 2

    resp1 = op.responses["200"]
    assert resp1.description == "pet response"
    assert len(resp1.content) == 1
    assert "application/json" in resp1.content
    con1 = resp1.content["application/json"]
    assert con1.schema_ is not None
    assert con1.schema_.type == "array"
    # we're not going to test that the ref resolved correctly here - that's a separate test
    assert type(con1.schema_.items._target) == Schema

    resp2 = op.responses["default"]
    assert resp2.description == "unexpected error"
    assert len(resp2.content) == 1
    assert "application/json" in resp2.content
    con2 = resp2.content["application/json"]
    assert con2.schema_ is not None
    # again, test ref resolution elsewhere
    assert type(con2.schema_._target) == Schema


def test_securityparameters(httpx_mock, with_securityparameters):
    api = OpenAPI(URLBASE, with_securityparameters, session_factory=httpx.Client)
    httpx_mock.add_response(headers={"Content-Type": "application/json"}, content=b"[]")

    auth = str(uuid.uuid4())

    for i in api.paths.values():
        if not i.post or not i.post.security:
            continue
        s = i.post.security[0]
        assert type(s.name) == str
        assert type(s.types) == list
        break
    else:
        assert False

    with pytest.raises(ValueError, match="does not accept security scheme xAuth"):
        api.authenticate("xAuth", auth)
        api._.api_v1_auth_login_info(data={}, parameters={})

    # global security
    api.authenticate("cookieAuth", auth)
    api._.api_v1_auth_login_info(data={}, parameters={})
    request = httpx_mock.get_requests()[-1]

    # path
    api.authenticate("tokenAuth", auth)
    api._.api_v1_auth_login_create(data={}, parameters={})
    request = httpx_mock.get_requests()[-1]
    assert request.headers["Authorization"] == auth

    api.authenticate("paramAuth", auth)
    api._.api_v1_auth_login_create(data={}, parameters={})
    request = httpx_mock.get_requests()[-1]
    assert yarl.URL(str(request.url)).query["auth"] == auth

    api.authenticate("cookieAuth", auth)
    api._.api_v1_auth_login_create(data={}, parameters={})
    request = httpx_mock.get_requests()[-1]
    assert request.headers["Cookie"] == "Session=%s" % (auth,)

    api.authenticate("basicAuth", (auth, auth))
    api._.api_v1_auth_login_create(data={}, parameters={})
    request = httpx_mock.get_requests()[-1]
    assert request.headers["Authorization"].split(" ")[1] == base64.b64encode((auth + ":" + auth).encode()).decode()

    api.authenticate("digestAuth", (auth, auth))
    api._.api_v1_auth_login_create(data={}, parameters={})
    request = httpx_mock.get_requests()[-1]
    # can't test?

    api.authenticate("bearerAuth", auth)
    api._.api_v1_auth_login_create(data={}, parameters={})
    request = httpx_mock.get_requests()[-1]
    assert request.headers["Authorization"] == "Bearer %s" % (auth,)

    # null session
    api.authenticate(None, None)
    api._.api_v1_auth_login_info(data={}, parameters={})


def test_parameters(httpx_mock, with_parameters):
    httpx_mock.add_response(headers={"Content-Type": "application/json"}, content=b"[]")
    api = OpenAPI(URLBASE, with_parameters, session_factory=httpx.Client)

    with pytest.raises(ValueError, match="Required parameter \w+ not provided"):
        api._.getTest(data={}, parameters={})

    Header = str([i ** i for i in range(3)])
    api._.getTest(data={}, parameters={"Cookie": "Cookie", "Path": "Path", "Header": Header, "Query": "Query"})
    request = httpx_mock.get_requests()[-1]

    assert request.headers["Header"] == Header
    assert request.headers["Cookie"] == "Cookie=Cookie"
    assert pathlib.Path(request.url.path).name == "Path"
    assert yarl.URL(str(request.url)).query["Query"] == "Query"
