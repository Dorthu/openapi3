import dataclasses
from typing import Union, Optional

from pydantic import Field

from .object_base import ObjectBase, Map

from .example import Example
from .paths import Reference, RequestBody, Link, Parameter, Response
from .schemas import Schema
from .security import SecurityScheme

class Components(ObjectBase):
    """
    A `Components Object`_ holds a reusable set of different aspects of the OAS
    spec.

    .. _Components Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#componentsObject
    """

    examples: Optional[Map[str, Union['Example', 'Reference']]] = Field(default=None)
    parameters: Optional[Map[str, Union['Parameter', 'Reference']]] = Field(default=None)
    requestBodies: Optional[Map[str, Union['RequestBody', 'Reference']]] = Field(default=None)
    responses: Optional[Map[str, Union['Response', 'Reference']]] = Field(default=None)
    schemas: Optional[Map[str, Union['Schema', 'Reference']]] = Field(default=None)
    securitySchemes: Optional[Map[str, Union['SecurityScheme', 'Reference']]] = Field(default=None)
    # headers: ['Header', 'Reference'], is_map=True
    links: Optional[Map[str, Union['Link', 'Reference']]] = Field(default=None)
    # callbacks: ['Callback', 'Reference'], is_map=True

Components.update_forward_refs()