from typing import Optional

from pydantic import Field

from .object_base import ObjectExtended
from .general import ExternalDocumentation


class Tag(ObjectExtended):
    """
    A `Tag Object`_ holds a reusable set of different aspects of the OAS
    spec.

    .. _Tag Object: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#tag-object
    """

    name: str = Field(...)
    description: Optional[str] = Field(default=None)
    externalDocs: Optional[ExternalDocumentation] = Field(default=None)
