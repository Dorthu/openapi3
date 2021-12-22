import dataclasses
from typing import Union

from .object_base import ObjectBase

@dataclasses.dataclass(init=False)
class Example(ObjectBase):
    """
    A `Example Object`_ holds a reusable set of different aspects of the OAS
    spec.

    .. _Example Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#exampleObject
    """
    __slots__ = ['summary', 'description', 'value', 'externalValue']

    summary: str
    description: str
    value: Union['Reference', dict, str] # 'any' type
    externalValue: str
