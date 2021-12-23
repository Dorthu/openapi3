import dataclasses
from typing import ForwardRef, Optional

from pydantic import Field

from .object_base import ObjectBase


class Info(ObjectBase):
    """
    An OpenAPI Info object, as defined in `the spec`_.

    .. _the spec: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#infoObject
    """

    title: str = Field(default=None)
    version: str = Field(default=None)

    contact: Optional[ForwardRef('Contact')] = Field(default=None)
    description: Optional[str] = Field(default=None)
    license: Optional[ForwardRef('License')] = Field(default=None)
    termsOfService: Optional[str] = Field(default=None)



class Contact(ObjectBase):
    """
    Contact object belonging to an Info object, as described `here`_

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#contactObject
    """

    email: str = Field(default=None)
    name: str = Field(default=None)
    url: str = Field(default=None)

class License(ObjectBase):
    """
    License object belonging to an Info object, as described `here`_

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#license-object
    """

    name: str = Field(default=None)
    url: Optional[str] = Field(default=None)

Info.update_forward_refs()
