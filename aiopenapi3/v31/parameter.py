from typing import Union, Optional, Dict, Any

from pydantic import Field

from ..base import ObjectExtended

from .example import Example
from .general import Reference
from .schemas import Schema


class ParameterBase(ObjectExtended):
    """
    A `Parameter Object`_ defines a single operation parameter.

    .. _Parameter Object: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#parameterObject
    """

    description: Optional[str] = Field(default=None)
    required: Optional[bool] = Field(default=None)
    deprecated: Optional[bool] = Field(default=None)
    allowEmptyValue: Optional[bool] = Field(default=None)

    style: Optional[str] = Field(default=None)
    explode: Optional[bool] = Field(default=None)
    allowReserved: Optional[bool] = Field(default=None)
    schema_: Optional[Schema] = Field(default=None, alias="schema")
    example: Optional[Any] = Field(default=None)
    examples: Optional[Dict[str, Union["Example", Reference]]] = Field(default_factory=dict)

    content: Optional[Dict[str, "MediaType"]]


class Parameter(ParameterBase):
    name: str = Field(required=True)
    in_: str = Field(required=True, alias="in")  # TODO must be one of ["query","header","path","cookie"]


class Header(ParameterBase):
    """

    .. _HeaderObject: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#headerObject
    """

    pass


from .media import MediaType

Parameter.update_forward_refs()
Header.update_forward_refs()
