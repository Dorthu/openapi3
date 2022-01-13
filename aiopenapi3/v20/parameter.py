from typing import Union, Optional, Any

from pydantic import Field

from .general import Reference
from .schemas import Schema
from ..base import ObjectExtended, ObjectBase


class Item(ObjectExtended):
    """
    https://swagger.io/specification/v2/#items-object
    """

    type: str = Field(...)
    format: Optional[str] = Field(default=None)
    items: Optional["Item"] = Field(default=None)
    collectionFormat: Optional[str] = Field(default=None)
    default: Any = Field(default=None)
    maximum: Optional[int] = Field(default=None)
    exclusiveMaximum: Optional[bool] = Field(default=None)
    minimum: Optional[int] = Field(default=None)
    exclusiveMinimum: Optional[bool] = Field(default=None)
    maxLength: Optional[int] = Field(default=None)
    minLength: Optional[int] = Field(default=None)
    pattern: Optional[str] = Field(default=None)
    maxItems: Optional[int] = Field(default=None)
    minItems: Optional[int] = Field(default=None)
    uniqueItems: Optional[bool] = Field(default=None)
    enum: Optional[Any] = Field(default=None)
    multipleOf: Optional[int] = Field(default=None)


class Empty(ObjectExtended):
    pass


class Parameter(ObjectExtended):
    """
    Describes a single operation parameter.

    .. _Parameter Object: https://swagger.io/specification/v2/#parameter-object
    """

    name: str = Field(required=True)
    in_: str = Field(required=True, alias="in")  # "query", "header", "path", "formData" or "body"

    description: Optional[str] = Field(default=None)
    required: Optional[bool] = Field(default=None)

    schema_: Optional[Union[Schema, Reference]] = Field(default=None, alias="schema")

    type: Optional[str] = Field(default=None)
    format: Optional[str] = Field(default=None)
    allowEmptyValue: Optional[bool] = Field(default=None)
    items: Optional[Union[Item, Empty]] = Field(default=None)
    collectionFormat: Optional[str] = Field(default=None)
    default: Any = Field(default=None)
    maximum: Optional[int] = Field(default=None)
    exclusiveMaximum: Optional[bool] = Field(default=None)
    minimum: Optional[int] = Field(default=None)
    exclusiveMinimum: Optional[bool] = Field(default=None)
    maxLength: Optional[int] = Field(default=None)
    minLength: Optional[int] = Field(default=None)
    pattern: Optional[str] = Field(default=None)
    maxItems: Optional[int] = Field(default=None)
    minItems: Optional[int] = Field(default=None)
    uniqueItems: Optional[bool] = Field(default=None)
    enum: Optional[Any] = Field(default=None)
    multipleOf: Optional[int] = Field(default=None)


class Header(ObjectExtended):
    """
    https://swagger.io/specification/v2/#header-object
    """

    description: Optional[str] = Field(default=None)

    type: str = Field(...)
    format: Optional[str] = Field(default=None)
    items: Optional[Item] = Field(default=None)
    collectionFormat: Optional[str] = Field(default=None)
    default: Any = Field(default=None)
    maximum: Optional[int] = Field(default=None)
    exclusiveMaximum: Optional[bool] = Field(default=None)
    minimum: Optional[int] = Field(default=None)
    exclusiveMinimum: Optional[bool] = Field(default=None)
    maxLength: Optional[int] = Field(default=None)
    minLength: Optional[int] = Field(default=None)
    pattern: Optional[str] = Field(default=None)
    maxItems: Optional[int] = Field(default=None)
    minItems: Optional[int] = Field(default=None)
    uniqueItems: Optional[bool] = Field(default=None)
    enum: Optional[Any] = Field(default=None)
    multipleOf: Optional[int] = Field(default=None)


Item.update_forward_refs()
