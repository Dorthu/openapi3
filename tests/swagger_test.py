import uuid

import yarl
import httpx
import pytest

from aiopenapi3 import OpenAPI

URLBASE = "/"


def test_parse_swagger(with_swagger):
    api = OpenAPI(URLBASE, with_swagger)


def test_swagger_url(with_swagger):
    api = OpenAPI(URLBASE, with_swagger)
    assert str(api.url) == "https://api.example.com/v1"


def test_securityparameters(httpx_mock, with_swagger):
    api = OpenAPI(URLBASE, with_swagger, session_factory=httpx.Client)
    user = api._.createUser.return_value().get_type().construct(name="test", id=1)
    httpx_mock.add_response(headers={"Content-Type": "application/json"}, json=user.dict())

    auth = str(uuid.uuid4())

    with pytest.raises(ValueError, match="does not accept security schemes \['xAuth'\]"):
        api.authenticate(xAuth=auth)
        api._.createUser(data=user, parameters={})

    # global security
    api.authenticate(None, BasicAuth=(auth, auth))
    api._.getUser(data={}, parameters={"userId": 1})
    request = httpx_mock.get_requests()[-1]

    # path
    api.authenticate(None, QueryAuth=auth)
    api._.createUser(data={}, parameters={})
    request = httpx_mock.get_requests()[-1]
    assert request.url.params["auth"] == auth

    # header
    api.authenticate(None, HeaderAuth="Bearer %s" % (auth,))
    api._.createUser(data={}, parameters={})
    request = httpx_mock.get_requests()[-1]
    assert request.headers["Authorization"] == "Bearer %s" % (auth,)

    # null session
    httpx_mock.add_response(headers={"Content-Type": "application/json"}, json=[user.dict()])
    api.authenticate(None)
    api._.listUsers(data={}, parameters={})


def test_combined_securityparameters(httpx_mock, with_swagger):
    api = OpenAPI(URLBASE, with_swagger, session_factory=httpx.Client)
    user = api._.createUser.return_value().get_type().construct(name="test", id=1)
    httpx_mock.add_response(headers={"Content-Type": "application/json"}, json=user.dict())

    api.authenticate(user="u")
    with pytest.raises(ValueError, match="No security requirement satisfied"):
        api._.combinedSecurity(data={}, parameters={})

    api.authenticate(**{"user": "u", "token": "t"})
    api._.combinedSecurity(data={}, parameters={})

    api.authenticate(None)
    with pytest.raises(ValueError, match="No security requirement satisfied"):
        api._.combinedSecurity(data={}, parameters={})


def test_post_body(httpx_mock, with_swagger):

    auth = str(uuid.uuid4())
    api = OpenAPI(URLBASE, with_swagger, session_factory=httpx.Client)
    user = api._.createUser.return_value().get_type().construct(name="test", id=1)
    httpx_mock.add_response(headers={"Content-Type": "application/json"}, json=user.dict())

    api.authenticate(HeaderAuth="Bearer %s" % (auth,))
    with pytest.raises(ValueError, match="Request Body is required but none was provided."):
        api._.createUser(data=None, parameters={})
    api._.createUser(data={}, parameters={})
    api._.createUser(data=user, parameters={})


def test_parameters(httpx_mock, with_swagger):
    api = OpenAPI(URLBASE, with_swagger, session_factory=httpx.Client)
    user = api._.createUser.return_value().get_type().construct(name="test", id=1)

    auth = str(uuid.uuid4())
    api.authenticate(BasicAuth=(auth, auth))

    with pytest.raises(ValueError, match="Required parameter \w+ not provided"):
        api._.getUser(data={}, parameters={})

    httpx_mock.add_response(headers={"Content-Type": "application/json"}, json=[user.dict()])
    api.authenticate(None)
    api._.listUsers(data={}, parameters={"inQuery": "Q", "inHeader": "H"})

    request = httpx_mock.get_requests()[-1]
    assert request.headers["inHeader"] == "H"
    assert yarl.URL(str(request.url)).query["inQuery"] == "Q"
