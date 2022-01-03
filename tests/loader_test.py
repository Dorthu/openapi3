from pathlib import Path
import json

import pytest
from aiopenapi3 import OpenAPI, FileSystemLoader, ReferenceResolutionError
from aiopenapi3.loader import Loader

SPECTPL = """
openapi: "3.0.0"
info:
  title: spec01
  version: 1.0.0
  description: | 
    {description}
  
paths:
  /load:
    get:
      responses:
        '200':
          $ref: {jsonref}
components:
  schemas:
     Example:
       type: str
     Object:
       type: object
       properties:
         name: 
            type: string
         value: 
            type: boolean     
"""

data = [("petstore-expanded.yaml#/components/schemas/Pet", None),
        ("no-such.file.yaml#/components/schemas/Pet", FileNotFoundError),
        ("petstore-expanded.yaml#/components/schemas/NoSuchPet", ReferenceResolutionError),]

@pytest.mark.parametrize("jsonref, exception", data)
def test_loader_jsonref(jsonref, exception):
    loader = FileSystemLoader(Path("tests/fixtures"))
    values = {"jsonref":jsonref, "description":""}
    if exception is None:
        api = OpenAPI.loads("loader.yaml", SPECTPL.format(**values), session_factory=None, loader=loader)
    else:
        with pytest.raises(exception):
            api = OpenAPI.loads("loader.yaml", SPECTPL.format(**values), session_factory=None, loader=loader)


def test_loader_decode():
    with pytest.raises(ValueError, match="encoding"):
        Loader.decode(b'rvice.\r\n    \xa9 2020, 3GPP Organ', codec="utf-8")

def test_loader_format():
    values = {"jsonref":"'#/components/schemas/Example'", "description":""}
    spec = SPECTPL.format(**values)
    api = OpenAPI.loads("loader.yaml", spec)

    spec = Loader.dict(Path("loader.yaml"), spec)
    spec = json.dumps(spec)
    api = OpenAPI.loads("loader.json", spec)