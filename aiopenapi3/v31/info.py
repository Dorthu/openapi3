from typing import Optional

from pydantic import Field

from aiopenapi3.base import ObjectExtended


from ..v30.info import Contact


class License(ObjectExtended):
    """
    License object belonging to an Info object, as described `here`_

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#license-object
    """

    name: str = Field(...)
    identifier: Optional[str] = Field(default=None)
    url: Optional[str] = Field(default=None)


class Info(ObjectExtended):
    """
    An OpenAPI Info object, as defined in `the spec`_.

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#info-object
    """

    title: str = Field(...)
    summary: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    termsOfService: Optional[str] = Field(default=None)
    contact: Optional[Contact] = Field(default=None)
    license: Optional[License] = Field(default=None)
    version: str = Field(...)
