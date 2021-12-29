import json

import pytest

import requests
import requests_mock

import tatsu
from openapi3.expression.grammar import loads

parse_testdata = [
    "$url",
    "$method",
    "$statusCode",
#    "$request.",
    "$request.body#/url",
]

@pytest.mark.parametrize("data", parse_testdata)
def test_parse(data):
    m = loads(data)
    assert m is not None

def test_parse_fail():
    with pytest.raises(tatsu.exceptions.FailedParse):
        loads("x")

get_testdata = {
    "$url":"http://example.org/subscribe/myevent?queryUrl=http://clientdomain.com/stillrunning",
    "$method":"POST",
    "$request.path.eventType":"myevent",
    "$request.query.queryUrl":"http://clientdomain.com/stillrunning",
    "$request.header.content-Type":"application/json",
    "$request.body#/failedUrl":"http://clientdomain.com/failed",
    "$request.body#/successUrls/2":"http://clientdomain.com/medium",
    "$response.header.Location":"http://example.org/subscription/1" ,
}
@pytest.mark.parametrize("param, result", get_testdata.items())
def test_get(param, result):
    url = "http://example.org/subscribe/myevent?queryUrl=http://clientdomain.com/stillrunning"
    data = {
        "failedUrl": "http://clientdomain.com/failed",
        "successUrls": [
            "http://clientdomain.com/fast",
            "http://clientdomain.com/medium",
            "http://clientdomain.com/slow"
        ]
    }

    with requests_mock.Mocker() as m:
        m.post(url, headers={"Location":"http://example.org/subscription/1"})
        req = requests.Request(method="POST", url=url, data=json.dumps(data), headers={"Content-Type":"application/json"})
        req = req.prepare()
        req.path = {"eventType":"myevent"}
        resp = requests.Session().send(req)

    m = loads(param)
    r = m.eval(req, resp)
    assert r == result
