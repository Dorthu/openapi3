import dataclasses
from typing import List, Optional
from .object_base import ObjectBase, Map


@dataclasses.dataclass
class Server(ObjectBase):
    """
    The Server object, as described `here`_

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#serverObject
    """

    url: str = dataclasses.field(default=None)
    description: Optional[str] = dataclasses.field(default=None)
    variables: Optional[Map[str, 'ServerVariable']] = dataclasses.field(default=None)


@dataclasses.dataclass
class ServerVariable(ObjectBase):
    """
    A ServerVariable object as defined `here`_.

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#server-variable-object
    """

    default: str = dataclasses.field(default=None)
    description: Optional[str] = dataclasses.field(default=None)
    enum: Optional[List[str]] = dataclasses.field(default=None)

