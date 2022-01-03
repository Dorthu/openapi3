from pydantic import Field

from .general import ObjectExtended


class XML(ObjectExtended):
    """

    .. XML Object: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#xml-object
    """

    name: str = Field(default=None)
    namespace: str = Field(default=None)
    prefix: str = Field(default=None)
    attribute: bool = Field(default=False)
    wrapped: bool = Field(default=False)
