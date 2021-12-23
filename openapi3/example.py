import dataclasses
from typing import Union, Optional

from pydantic import Field

from .object_base import ObjectBase


class Example(ObjectBase):
    """
    A `Example Object`_ holds a reusable set of different aspects of the OAS
    spec.

    .. _Example Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#exampleObject
    """

    summary: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    value: Optional[Union['Reference', dict, str]] = Field(default=None) # 'any' type
    externalValue: Optional[str] = Field(default=None)
