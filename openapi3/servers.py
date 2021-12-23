import dataclasses
from typing import List, Optional, ForwardRef

from pydantic import Field

from .object_base import ObjectBase, Map



class Server(ObjectBase):
    """
    The Server object, as described `here`_

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#serverObject
    """

    url: str = Field(default=None)
    description: Optional[str] = Field(default=None)
    variables: Optional[Map[str, ForwardRef('ServerVariable')]] = Field(default=None)



class ServerVariable(ObjectBase):
    """
    A ServerVariable object as defined `here`_.

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#server-variable-object
    """

    default: str = Field(default=None)
    description: Optional[str] = Field(default=None)
    enum: Optional[List[str]] = Field(default=None)

