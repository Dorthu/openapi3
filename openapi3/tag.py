import dataclasses
from typing import Optional
from .object_base import ObjectBase

@dataclasses.dataclass
class Tag(ObjectBase):
    """
    A `Tag Object`_ holds a reusable set of different aspects of the OAS
    spec.

    .. _Tag Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#tagObject
    """
#    __slots__ = ['name', 'description', 'externalDocs']

    name: Optional[str] = dataclasses.field(default=None)
    description: Optional[str] = dataclasses.field(default=None)
    externalDocs: Optional[str] = dataclasses.field(default=None)
