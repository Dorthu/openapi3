from pydantic import Field

from .general import ObjectExtended


class XML(ObjectExtended):
    """
    A metadata object that allows for more fine-tuned XML model definitions.

    https://swagger.io/specification/v2/#xml-object
    """

    name: str = Field(default=None)
    namespace: str = Field(default=None)
    prefix: str = Field(default=None)
    attribute: bool = Field(default=False)
    wrapped: bool = Field(default=False)
