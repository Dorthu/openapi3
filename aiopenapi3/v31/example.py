from ..v30.example import Example as Example30

from typing import Union, Optional

from pydantic import Field

from .general import Reference


class Example(Example30):
    """
    A `Example Object`_ holds a reusable set of different aspects of the OAS
    spec.

    .. _Example Object: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#exampleObject
    """

    value: Optional[Union[Reference, dict, str]] = Field(default=None)  # 'any' type
