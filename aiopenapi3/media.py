from typing import Union, Optional, Dict, Any

from pydantic import Field

from .example import Example
from .general import Reference
from .object_base import ObjectExtended
from .schemas import Schema


class Encoding(ObjectExtended):
    """
    A single encoding definition applied to a single schema property.

    .. _Encoding: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#encoding-object
    """

    contentType: Optional[str] = Field(default=None)
    headers: Optional[Dict[str, Union["Header", Reference]]] = Field(default_factory=dict)
    style: Optional[str] = Field(default=None)
    explode: Optional[bool] = Field(default=None)
    allowReserved: Optional[bool] = Field(default=None)


class MediaType(ObjectExtended):
    """
    A `MediaType`_ object provides schema and examples for the media type identified
    by its key.  These are used in a RequestBody object.

    .. _MediaType: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#media-type-object
    """

    schema_: Optional[Union[Schema, Reference]] = Field(required=True, alias="schema")
    example: Optional[Any] = Field(default=None)  # 'any' type
    examples: Optional[Dict[str, Union[Example, Reference]]] = Field(default_factory=dict)
    encoding: Optional[Dict[str, Encoding]] = Field(default_factory=dict)


from .parameter import Header

Encoding.update_forward_refs()
