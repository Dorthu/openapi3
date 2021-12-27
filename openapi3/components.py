import dataclasses
from typing import Union, Optional, Dict

from pydantic import Field

from .object_base import ObjectBase

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

    examples: Optional[Dict[str, Union['Example', 'Reference']]] = Field(default_factory=dict)
    parameters: Optional[Dict[str, Union['Parameter', 'Reference']]] = Field(default_factory=dict)
    requestBodies: Optional[Dict[str, Union['RequestBody', 'Reference']]] = Field(default_factory=dict)
    responses: Optional[Dict[str, Union['Response', 'Reference']]] = Field(default_factory=dict)
    schemas: Optional[Dict[str, Union['Schema', 'Reference']]] = Field(default_factory=dict)
    securitySchemes: Optional[Dict[str, Union['SecurityScheme', 'Reference']]] = Field(default_factory=dict)
    # headers: ['Header', 'Reference'], is_map=True
    links: Optional[Dict[str, Union['Link', 'Reference']]] = Field(default_factory=dict)
    # callbacks: ['Callback', 'Reference'], is_map=True

Components.update_forward_refs()