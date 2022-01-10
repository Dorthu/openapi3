from ..v30.servers import Server

from typing import List, Optional, Dict

from pydantic import Field, root_validator

from ..base import ObjectExtended


class ServerVariable(ObjectExtended):
    """
    A ServerVariable object as defined `here`_.

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#server-variable-object
    """

    enum: Optional[List[str]] = Field(default=None)
    default: str = Field(...)
    description: Optional[str] = Field(default=None)

    @root_validator
    def validate_ServerVariable(cls, values):
        assert isinstance(values.get("enum", None), (list, None.__class__))

        # default value must be in enum
        assert values.get("default", None) in values.get("enum", [None])
        return values


class Server(ObjectExtended):
    """
    The Server object, as described `here`_

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#server-object
    """

    url: str = Field(...)
    description: Optional[str] = Field(default=None)
    variables: Optional[Dict[str, ServerVariable]] = Field(default_factory=dict)
