import json
import sys

import httpx
import pytest

import tatsu
from aiopenapi3.expression.grammar import loads

not310 = pytest.mark.skipif(
    sys.version_info >= (3, 10, 0), reason="tatsu 5.7 requires 3.10, we rely on 5.6"
)

parse_testdata = [
    "$url",
    "$method",
    "$statusCode",
#    "$request.",
    "$request.body#/url",
]

@not310
@pytest.mark.parametrize("data", parse_testdata)
def test_parse(data):
    m = loads(data)
    assert m is not None

@not310
def test_parse_fail():
    with pytest.raises(tatsu.exceptions.FailedParse):
        loads("$request.body#/~test")

@not310
def test_parse_escape():
    loads("$request.body#/~0test")
    loads("$request.body#/~1test")
    with pytest.raises(tatsu.exceptions.FailedParse):
        loads("$request.body#/~2test")
    with pytest.raises(tatsu.exceptions.FailedParse):
        loads("$request.body#/test/~")




get_testdata = {
    "$url":"http://example.org/subscribe/myevent?queryUrl=http://clientdomain.com/stillrunning",
    "$method":"POST",
    "$request.path.eventType":"myevent",
    "$request.query.queryUrl":"http://clientdomain.com/stillrunning",
    "$request.header.content-Type":"application/json",
    "$request.body#/failedUrl":"http://clientdomain.com/failed",
    "$request.body#/successUrls/2":"http://clientdomain.com/medium",
    "$response.header.Location":"http://example.org/subscription/1" ,
    "$request.body#/escaped~1content/2/~0/~1/y":"yes",
    "$request.body#/escaped~0content/2/~1/~0/x":"no",
}

@not310
@pytest.mark.parametrize("param, result", get_testdata.items())
def test_get(httpx_mock, param, result):
    url = "http://example.org/subscribe/myevent?queryUrl=http://clientdomain.com/stillrunning"
    data = {
        "failedUrl": "http://clientdomain.com/failed",
        "successUrls": [
            "http://clientdomain.com/fast",
            "http://clientdomain.com/medium",
            "http://clientdomain.com/slow"
        ],
        "escaped/content": [0, {"~": {"/": {"y": "yes"}}}],
        "escaped~content": [0, {"/": {"~": {"x": "no" }}}]
    }

    httpx_mock.add_response(headers={"Location":"http://example.org/subscription/1"},)
    client = httpx.Client()
    resp = client.post(url, json=data, headers={"Location":"http://example.org/subscription/1", "Content-Type":"application/json"})

    req = httpx_mock.get_requests()[-1]
    req.path = {"eventType":"myevent"}

    m = loads(param)
    r = m.eval(req, resp)
    assert r == result
