import dataclasses
from typing import Union, Optional

from .object_base import ObjectBase

@dataclasses.dataclass
class Example(ObjectBase):
    """
    A `Example Object`_ holds a reusable set of different aspects of the OAS
    spec.

    .. _Example Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#exampleObject
    """
#    __slots__ = ['summary', 'description', 'value', 'externalValue']

    summary: Optional[str] = dataclasses.field(default=None)
    description: Optional[str] = dataclasses.field(default=None)
    value: Optional[Union['Reference', dict, str]] = dataclasses.field(default=None) # 'any' type
    externalValue: Optional[str] = dataclasses.field(default=None)
