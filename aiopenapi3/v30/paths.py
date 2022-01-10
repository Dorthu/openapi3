from typing import Union, List, Optional, Dict

from pydantic import Field, BaseModel, root_validator

from ..base import ObjectBase, ObjectExtended
from ..errors import SpecError
from .general import ExternalDocumentation
from .general import Reference
from .media import MediaType
from .parameter import Header, Parameter
from .servers import Server
from .security import SecurityRequirement


class RequestBody(ObjectExtended):
    """
    A `RequestBody`_ object describes a single request body.

    .. _RequestBody: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#requestBodyObject
    """

    description: Optional[str] = Field(default=None)
    content: Dict[str, MediaType] = Field(...)
    required: Optional[bool] = Field(default=False)


class Link(ObjectExtended):
    """
    A `Link Object`_ describes a single Link from an API Operation Response to an API Operation Request

    .. _Link Object: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#link-object
    """

    operationRef: Optional[str] = Field(default=None)
    operationId: Optional[str] = Field(default=None)
    parameters: Optional[Dict[str, Union["RuntimeExpression", str]]] = Field(default=None)
    requestBody: Optional[dict] = Field(default=None)
    description: Optional[str] = Field(default=None)
    server: Optional[Server] = Field(default=None)

    @root_validator(pre=False)
    def validate_Link_operation(cls, values):
        if values["operationId"] != None and values["operationRef"] != None:
            raise SpecError("operationId and operationRef are mutually exclusive, only one of them is allowed")

        if values["operationId"] == values["operationRef"] == None:
            raise SpecError("operationId and operationRef are mutually exclusive, one of them must be specified")

        return values


class Response(ObjectExtended):
    """
    A `Response Object`_ describes a single response from an API Operation,
    including design-time, static links to operations based on the response.

    .. _Response Object: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#responses-object
    """

    description: str = Field(...)
    headers: Optional[Dict[str, Union[Header, Reference]]] = Field(default_factory=dict)
    content: Optional[Dict[str, MediaType]] = Field(default_factory=dict)
    links: Optional[Dict[str, Union[Link, Reference]]] = Field(default_factory=dict)


class Operation(ObjectExtended):
    """
    An Operation object as defined `here`_

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#operation-object
    """

    tags: Optional[List[str]] = Field(default=None)
    summary: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    externalDocs: Optional[ExternalDocumentation] = Field(default=None)
    operationId: Optional[str] = Field(default=None)
    parameters: Optional[List[Union[Parameter, Reference]]] = Field(default_factory=list)
    requestBody: Optional[Union[RequestBody, Reference]] = Field(default=None)
    responses: Dict[str, Union[Response, Reference]] = Field(...)
    callbacks: Optional[Dict[str, Union["Callback", Reference]]] = Field(default_factory=dict)
    deprecated: Optional[bool] = Field(default=None)
    security: Optional[List[SecurityRequirement]] = Field(default_factory=list)
    servers: Optional[List[Server]] = Field(default=None)


class PathItem(ObjectExtended):
    """
    A Path Item, as defined `here`_.
    Describes the operations available on a single path.

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#paths-object
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


class Callback(ObjectBase):
    """
    A map of possible out-of band callbacks related to the parent operation.

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#callback-object

    This object MAY be extended with Specification Extensions.
    """

    __root__: Dict[str, PathItem]


class RuntimeExpression(ObjectBase):
    """


    .. Runtime Expression: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#runtime-expressions
    """

    __root__: str = Field(...)


Operation.update_forward_refs()
Link.update_forward_refs()