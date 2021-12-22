import dataclasses
from typing import List
from .object_base import ObjectBase, Map


@dataclasses.dataclass(init=False)
class Server(ObjectBase):
    """
    The Server object, as described `here`_

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#serverObject
    """
    __slots__ = ['url', 'description', 'variables']
    required_fields = ['url']

    description: str
    url: str
    variables: Map[str, 'ServerVariable']


@dataclasses.dataclass(init=False)
class ServerVariable(ObjectBase):
    """
    A ServerVariable object as defined `here`_.

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#server-variable-object
    """
    __slots__ = ['enum', 'default', 'description']
    required_fields = ['default']

    default: str
    description: str
    enum: List[str]

