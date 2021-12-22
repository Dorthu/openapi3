import dataclasses
from typing import ForwardRef
from .object_base import ObjectBase

@dataclasses.dataclass(init=False)
class Info(ObjectBase):
    """
    An OpenAPI Info object, as defined in `the spec`_.

    .. _the spec: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#infoObject
    """
    __slots__ = ['title', 'description', 'termsOfService', 'contact',
                 'license', 'version']
    required_fields = ['title', 'version']

    contact: ForwardRef('Contact')
    description: str
    license: ForwardRef('License')
    termsOfService: str
    title: str
    version: str

@dataclasses.dataclass(init=False)
class Contact(ObjectBase):
    """
    Contact object belonging to an Info object, as described `here`_

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#contactObject
    """
    __slots__ = ['name', 'url', 'email']
    required_fields = ['name', 'url', 'email']

    email: str
    name: str
    url: str


@dataclasses.dataclass(init=False)
class License(ObjectBase):
    """
    License object belonging to an Info object, as described `here`_

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#license-object
    """
    __slots__ = ['name', 'url']
    required_fields = ['name']

    name: str
    url: str
