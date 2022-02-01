from typing import Union, List, Optional, Dict, Any

from pydantic import Field, root_validator

from .general import ExternalDocumentation
from .general import Reference
from .parameter import Header, Parameter
from .schemas import Schema
from .security import SecurityRequirement
from ..base import ObjectExtended, ObjectBase, PathsBase


class Response(ObjectExtended):
    """
    Describes a single response from an API Operation.

    .. _Response Object: https://swagger.io/specification/v2/#response-object
    """

    description: str = Field(...)
    schema_: Optional[Schema] = Field(default=None, alias="schema")
    headers: Optional[Dict[str, Header]] = Field(default_factory=dict)
    examples: Optional[Dict[str, Any]] = Field(default=None)


class Operation(ObjectExtended):
    """
    An Operation object as defined `here`_

    .. _here: https://swagger.io/specification/v2/#operation-object
    """

    tags: Optional[List[str]] = Field(default=None)
    summary: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    externalDocs: Optional[ExternalDocumentation] = Field(default=None)
    operationId: Optional[str] = Field(default=None)
    consumes: Optional[List[str]] = Field(default_factory=list)
    produces: Optional[List[str]] = Field(default_factory=list)
    parameters: Optional[List[Union[Parameter, Reference]]] = Field(default_factory=list)
    responses: Dict[str, Union[Reference, Response]] = Field(default_factory=dict)
    schemes: Optional[List[str]] = Field(default_factory=list)
    deprecated: Optional[bool] = Field(default=None)
    security: Optional[List[SecurityRequirement]] = Field(default=None)


class PathItem(ObjectExtended):
    """
    A Path Item, as defined `here`_.
    Describes the operations available on a single path.

    .. _here: https://swagger.io/specification/v2/#path-item-object
    """

    ref: Optional[str] = Field(default=None, alias="$ref")
    get: Optional[Operation] = Field(default=None)
    put: Optional[Operation] = Field(default=None)
    post: Optional[Operation] = Field(default=None)
    delete: Optional[Operation] = Field(default=None)
    options: Optional[Operation] = Field(default=None)
    head: Optional[Operation] = Field(default=None)
    patch: Optional[Operation] = Field(default=None)
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


Operation.update_forward_refs()
