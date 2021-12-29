import urllib.parse
from typing import Optional

from pydantic import Field, Extra
from yarl import URL

from .object_base import ObjectExtended, ObjectBase


class ExternalDocumentation(ObjectExtended):
    """
    An `External Documentation Object`_ references external resources for extended
    documentation.

    .. _External Documentation Object: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#external-documentation-object
    """

    url: str = Field(...)
    description: Optional[str] = Field(default=None)


class JSONPointer:
    @staticmethod
    def decode(part):
        """

        https://swagger.io/docs/specification/using-ref/
        :param part:
        """
        part = urllib.parse.unquote(part)
        part = part.replace('~1', '/')
        return part.replace('~0', '~')

class JSONReference:
    @staticmethod
    def split(url):
        u = URL(url)
        return str(u.with_fragment("")), u.raw_fragment

class Reference(ObjectBase):
    """
    A `Reference Object`_ designates a reference to another node in the specification.

    .. _Reference Object: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#reference-object
    """
    ref: str = Field(alias="$ref")

    class Config:
        """This object cannot be extended with additional properties and any properties added SHALL be ignored."""
        extra = Extra.ignore
