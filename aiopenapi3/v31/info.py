from typing import Optional

from pydantic import Field, AnyUrl, EmailStr, root_validator

from aiopenapi3.base import ObjectExtended


class Contact(ObjectExtended):
    """
    Contact object belonging to an Info object, as described `here`_

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#contactObject
    """

    email: EmailStr = Field(default=None)
    name: str = Field(default=None)
    url: AnyUrl = Field(default=None)


class License(ObjectExtended):
    """
    License object belonging to an Info object, as described `here`_

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#license-object
    """

    name: str = Field(...)
    identifier: Optional[str] = Field(default=None)
    url: Optional[AnyUrl] = Field(default=None)

    @root_validator
    def validate_License(cls, values):

        """
        A URL to the license used for the API. This MUST be in the form of a URL. The url field is mutually exclusive of the identifier field.
        """
        assert not all([values.get(i, None) is not None for i in ["identifier", "url"]])
        return values


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
