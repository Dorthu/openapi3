import dataclasses
from typing import ForwardRef, Optional
from .object_base import ObjectBase

@dataclasses.dataclass
class Info(ObjectBase):
    """
    An OpenAPI Info object, as defined in `the spec`_.

    .. _the spec: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#infoObject
    """
#    __slots__ = ['title', 'description', 'termsOfService', 'contact',
#                 'license', 'version']
    required_fields = ['title', 'version']

    title: str = dataclasses.field(default=None)
    version: str = dataclasses.field(default=None)

    contact: Optional[ForwardRef('Contact')] = dataclasses.field(default=None)
    description: Optional[str] = dataclasses.field(default=None)
    license: Optional[ForwardRef('License')] = dataclasses.field(default=None)
    termsOfService: Optional[str] = dataclasses.field(default=None)

@dataclasses.dataclass
class Contact(ObjectBase):
    """
    Contact object belonging to an Info object, as described `here`_

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#contactObject
    """
#    __slots__ = ['name', 'url', 'email']
    required_fields = ['name', 'url', 'email']

    email: str = dataclasses.field(default=None)
    name: str = dataclasses.field(default=None)
    url: str = dataclasses.field(default=None)


@dataclasses.dataclass
class License(ObjectBase):
    """
    License object belonging to an Info object, as described `here`_

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#license-object
    """
#    __slots__ = ['name', 'url']
    required_fields = ['name']

    name: str = dataclasses.field(default=None)
    url: Optional[str] = dataclasses.field(default=None)
