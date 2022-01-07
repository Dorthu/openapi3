from typing import Union, Optional

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
    value: Optional[Union[Reference, dict, str]] = Field(default=None)  # 'any' type
    externalValue: Optional[str] = Field(default=None)
