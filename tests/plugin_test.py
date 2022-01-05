import httpx
from pathlib import Path

import yarl

from aiopenapi3 import FileSystemLoader, OpenAPI
from aiopenapi3.plugin import Init, Message, Document


class OnInit(Init):
    def initialized(self, ctx):
        ctx.initialized.paths["/pets"].get.operationId = "listPets"
        return ctx


class OnDocument(Document):
    def loaded(self, ctx):
        return ctx

    def parsed(self, ctx):
        if ctx.url == "test.yaml":
            ctx.document["components"] = {
                "schemas": {"Pet": {"$ref": "petstore-expanded.yaml#/components/schemas/Pet"}}
            }
            ctx.document["servers"] = [{"url": "/"}]
        elif ctx.url == "petstore-expanded.yaml":

            ctx.document["components"]["schemas"]["Pet"]["allOf"].append(
                {
                    "type": "object",
                    "required": ["color"],
                    "properties": {
                        "color": {"type": "string", "default": "blue"},
                        "weight": {"type": "integer", "default": 10},
                    },
                }
            )
        else:
            raise ValueError(ctx.url)

        return ctx


class OnMessage(Message):
    def marshalled(self, ctx):
        return ctx

    def sending(self, ctx):
        return ctx

    def received(self, ctx):
        ctx.received = """[{"id":1,"name":"theanimal"}]"""
        return ctx

    def parsed(self, ctx):
        if ctx.operationId == "listPets":
            if ctx.parsed[0].get("color", None) is None:
                ctx.parsed[0]["color"] = "red"

            if ctx.parsed[0]["id"] == 1:
                ctx.parsed[0]["id"] = 2
        return ctx

    def unmarshalled(self, ctx):
        if ctx.operationId == "listPets":
            if ctx.unmarshalled[0].id == 2:
                ctx.unmarshalled[0].id = 3
        return ctx


SPEC = """
openapi: 3.0.3
info:
  title: ''
  version: 0.0.0
paths:
  /pets:
    get:
      description: ''
      operationId: xPets
      responses:
        '200':
          description: pet response
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Pet'
"""


def test_Plugins(httpx_mock):
    httpx_mock.add_response(headers={"Content-Type": "application/json"}, content=b"[]")
    plugins = [OnInit(), OnDocument(), OnMessage()]
    api = OpenAPI.loads(
        "test.yaml",
        SPEC,
        plugins=plugins,
        loader=FileSystemLoader(Path().cwd() / "tests/fixtures"),
        session_factory=httpx.Client,
    )
    api._base_url = yarl.URL("http://127.0.0.1:80")
    r = api._.listPets()
    assert r

    item = r[0]
    assert item.id == 3
    assert item.weight == None  # default does not apply as it it unsed
    assert item.color == "red"  # default does not apply
