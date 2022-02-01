from typing import Union, List, Optional, Dict, Any

from pydantic import Field, root_validator, validator

from ..base import ObjectBase, ObjectExtended, PathsBase
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

    .. _Link Object: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#link-object
    """

    operationRef: Optional[str] = Field(default=None)
    operationId: Optional[str] = Field(default=None)
    parameters: Optional[Dict[str, Union[str, Any, "RuntimeExpression"]]] = Field(default=None)
    requestBody: Optional[Union[Any, "RuntimeExpression"]] = Field(default=None)
    description: Optional[str] = Field(default=None)
    server: Optional[Server] = Field(default=None)

    @root_validator
    def validate_Link_operation(cls, values):
        operationId, operationRef = (values.get(i, None) for i in ["operationId", "operationRef"])
        assert not (
            operationId != None and operationRef != None
        ), "operationId and operationRef are mutually exclusive, only one of them is allowed"
        assert not (
            operationId == operationRef == None
        ), "operationId and operationRef are mutually exclusive, one of them must be specified"
        return values


class Response(ObjectExtended):
    """
    A `Response Object`_ describes a single response from an API Operation,
    including design-time, static links to operations based on the response.

    .. _Response Object: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#responseObject
    """

    description: str = Field(...)
    headers: Optional[Dict[str, Union[Header, Reference]]] = Field(default_factory=dict)
    content: Optional[Dict[str, MediaType]] = Field(default_factory=dict)
    links: Optional[Dict[str, Union[Link, Reference]]] = Field(default_factory=dict)


class Operation(ObjectExtended):
    """
    An Operation object as defined `here`_

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#operationObject
    """

    tags: Optional[List[str]] = Field(default=None)
    summary: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    externalDocs: Optional[ExternalDocumentation] = Field(default=None)
    operationId: Optional[str] = Field(default=None)
    parameters: Optional[List[Union[Parameter, Reference]]] = Field(default_factory=list)
    requestBody: Optional[Union[RequestBody, Reference]] = Field(default=None)
    responses: Dict[str, Union[Response, Reference]] = Field(default_factory=dict)
    callbacks: Optional[Dict[str, Union["Callback", Reference]]] = Field(default_factory=dict)
    deprecated: Optional[bool] = Field(default=None)
    security: Optional[List[SecurityRequirement]] = Field(default_factory=list)
    servers: Optional[List[Server]] = Field(default=None)


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


class Paths(PathsBase):
    @root_validator(pre=True)
    def validate_Paths(cls, values):
        assert set(values.keys()) - frozenset(["__root__"]) == set([])
        p = {}
        e = {}
        for k, v in values.get("__root__", {}).items():
            if k[:2] == "x-":
                e[k] = v
            else:
                p[k] = PathItem(**v)
        return {"_paths": p, "_extensions": e}


class Callback(ObjectBase):
    """
    A map of possible out-of band callbacks related to the parent operation.

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#callback-object

    This object MAY be extended with Specification Extensions.
    """

    __root__: Dict[str, PathItem]


class RuntimeExpression(ObjectBase):
    """


    .. Runtime Expression: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#runtimeExpression
    """

    __root__: str = Field(...)


Operation.update_forward_refs()
Link.update_forward_refs()
