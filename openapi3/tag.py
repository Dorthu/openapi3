import dataclasses
from typing import Optional

from pydantic import Field

from .object_base import ObjectBase


class Tag(ObjectBase):
    """
    A `Tag Object`_ holds a reusable set of different aspects of the OAS
    spec.

    .. _Tag Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#tagObject
    """

    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    externalDocs: Optional[str] = Field(default=None)
