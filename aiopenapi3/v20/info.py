from typing import Optional

from pydantic import Field

from ..base import ObjectExtended


class Contact(ObjectExtended):
    """
    Contact object belonging to an Info object, as described `here`_

    .. _here: https://swagger.io/specification/v2/#contact-object
    """

    email: str = Field(default=None)
    name: str = Field(default=None)
    url: str = Field(default=None)


class License(ObjectExtended):
    """
    License object belonging to an Info object, as described `here`_

    .. _here: https://swagger.io/specification/v2/#license-object
    """

    name: str = Field(...)
    url: Optional[str] = Field(default=None)


class Info(ObjectExtended):
    """
    An OpenAPI Info object, as defined in `the spec`_.

    .. _here: https://swagger.io/specification/v2/#info-object
    """

    title: str = Field(...)
    description: Optional[str] = Field(default=None)
    termsOfService: Optional[str] = Field(default=None)
    license: Optional[License] = Field(default=None)
    contact: Optional[Contact] = Field(default=None)
    version: str = Field(...)
