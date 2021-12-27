import dataclasses
from typing import Optional

from pydantic import Field, root_validator

from .object_base import ObjectBase


class ExternalDocumentation(ObjectBase):
    """
    An `External Documentation Object`_ references external resources for extended
    documentation.

    .. _External Documentation Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#externalDocumentationObject
    """

    url: str

    description: Optional[str] = Field(default=None)



class Reference(ObjectBase):
    """
    A `Reference Object`_ designates a reference to another node in the specification.

    .. _Reference Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#referenceObject
    """
    ref: str = Field(alias="$ref")

#    @root_validator
#    def root_check(cls, values):
#        print(values)
#        return values