from typing import Union, Optional, Dict

from pydantic import Field

from ..base import ObjectExtended

from .example import Example
from .paths import RequestBody, Link, Response, Callback
from .general import Reference
from .parameter import Header, Parameter
from .schemas import Schema
from .security import SecurityScheme


class Components(ObjectExtended):
    """
    A `Components Object`_ holds a reusable set of different aspects of the OAS
    spec.

    .. _Components Object: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#components-object
    """

    schemas: Optional[Dict[str, Union[Schema, Reference]]] = Field(default_factory=dict)
    responses: Optional[Dict[str, Union[Response, Reference]]] = Field(default_factory=dict)
    parameters: Optional[Dict[str, Union[Parameter, Reference]]] = Field(default_factory=dict)
    examples: Optional[Dict[str, Union[Example, Reference]]] = Field(default_factory=dict)
    requestBodies: Optional[Dict[str, Union[RequestBody, Reference]]] = Field(default_factory=dict)
    headers: Optional[Dict[str, Union[Header, Reference]]] = Field(default_factory=dict)
    securitySchemes: Optional[Dict[str, Union[SecurityScheme, Reference]]] = Field(default_factory=dict)
    links: Optional[Dict[str, Union[Link, Reference]]] = Field(default_factory=dict)
    callbacks: Optional[Dict[str, Union[Callback, Reference]]] = Field(default_factory=dict)


#    pathItems: Optional[Dict[str, Union[PathItem, Reference]]] = Field(default_factory=dict) #v3.1

Components.update_forward_refs()
