from typing import Optional, Any

from pydantic import Field

from ..base import ObjectExtended

from .general import Reference


class Example(ObjectExtended):
    """
    A `Example Object`_ holds a reusable set of different aspects of the OAS
    spec.

    .. _Example Object: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#example-object
    """

    summary: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    value: Optional[Any] = Field(default=None)
    externalValue: Optional[str] = Field(default=None)
