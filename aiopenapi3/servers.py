from typing import List, Optional, Dict

from pydantic import Field

from .object_base import ObjectExtended


class ServerVariable(ObjectExtended):
    """
    A ServerVariable object as defined `here`_.

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#server-variable-object
    """

    enum: Optional[List[str]] = Field(default=None)
    default: str = Field(...)
    description: Optional[str] = Field(default=None)


class Server(ObjectExtended):
    """
    The Server object, as described `here`_

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#server-object
    """

    url: str = Field(...)
    description: Optional[str] = Field(default=None)
    variables: Optional[Dict[str, ServerVariable]] = Field(default_factory=dict)
