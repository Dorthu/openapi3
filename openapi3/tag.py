import dataclasses

from .object_base import ObjectBase

@dataclasses.dataclass(init=False)
class Tag(ObjectBase):
    """
    A `Tag Object`_ holds a reusable set of different aspects of the OAS
    spec.

    .. _Tag Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#tagObject
    """
    __slots__ = ['name', 'description', 'externalDocs']

    name: str
    description: str
    externalDocs: str
