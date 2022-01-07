from typing import Optional, List, Union, Dict

from pydantic import Field

from ..base import ObjectExtended

from .general import ExternalDocumentation, Reference
from .parameter import Parameter
from .servers import Server
from .media import MediaType
from .parameter import Header
from ..v30.paths import (
    Link,
    Callback,
    RuntimeExpression,
    RequestBody as RequestBody30,
    Operation as Operation30,
    Response as Response30,
)


class RequestBody(RequestBody30):
    """
    A `RequestBody`_ object describes a single request body.

    .. _RequestBody: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#requestBodyObject
    """

    content: Dict[str, MediaType] = Field(...)


class Response(Response30):
    headers: Optional[Dict[str, Union[Header, Reference]]] = Field(default_factory=dict)
    links: Optional[Dict[str, Union[Link, Reference]]] = Field(default_factory=dict)


class Operation(Operation30):
    """
    An Operation object as defined `here`_

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#operationObject
    """

    tags: Optional[List[str]] = Field(default=None)

    parameters: Optional[List[Union[Parameter, Reference]]] = Field(default_factory=list)
    requestBody: Optional[Union[RequestBody, Reference]] = Field(default=None)
    responses: Optional[Dict[str, Union[Response, Reference]]] = Field(default_factory=dict)
    callbacks: Optional[Dict[str, Union["Callback", Reference]]] = Field(default_factory=dict)


class PathItem(ObjectExtended):
    """
    A Path Item, as defined `here`_.
    Describes the operations available on a single path.

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#pathItemObject
    """

    ref: Optional[str] = Field(default=None, alias="$ref")
    summary: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    get: Optional[Operation] = Field(default=None)
    put: Optional[Operation] = Field(default=None)
    post: Optional[Operation] = Field(default=None)
    delete: Optional[Operation] = Field(default=None)
    options: Optional[Operation] = Field(default=None)
    head: Optional[Operation] = Field(default=None)
    patch: Optional[Operation] = Field(default=None)
    trace: Optional[Operation] = Field(default=None)
    servers: Optional[List[Server]] = Field(default=None)
    parameters: Optional[List[Union[Parameter, Reference]]] = Field(default_factory=list)
