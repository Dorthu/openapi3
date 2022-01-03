from typing import Union, Optional, Dict, Any

from pydantic import Field, root_validator

from .example import Example
from .general import Reference
from .object_base import ObjectExtended
from .schemas import Schema
from .media import MediaType


class ParameterBase(ObjectExtended):
    """
    A `Parameter Object`_ defines a single operation parameter.

    .. _Parameter Object: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#external-documentation-object
    """

    description: Optional[str] = Field(default=None)
    required: Optional[bool] = Field(default=None)
    deprecated: Optional[bool] = Field(default=None)
    allowEmptyValue: Optional[bool] = Field(default=None)

    style: Optional[str] = Field(default=None)
    explode: Optional[bool] = Field(default=None)
    allowReserved: Optional[bool] = Field(default=None)
    schema_: Optional[Union[Schema, Reference]] = Field(default=None, alias="schema")
    example: Optional[Any] = Field(default=None)
    examples: Optional[Dict[str, Union["Example", Reference]]] = Field(default_factory=dict)

    content: Optional[Dict[str, "MediaType"]]

    @root_validator
    def validate_ParameterBase(cls, values):
        #        if values["in_"] ==
        #        if self.in_ == "path" and self.required is not True:
        #            err_msg = 'Parameter {} must be required since it is in the path'
        #            raise SpecError(err_msg.format(self.get_path()), path=self._path)
        return values


class Parameter(ParameterBase):
    name: str = Field(required=True)
    in_: str = Field(required=True, alias="in")  # TODO must be one of ["query","header","path","cookie"]


class Header(ParameterBase):
    """

    .. _HeaderObject: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#header-object
    """
