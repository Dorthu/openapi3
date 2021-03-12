from .object_base import ObjectBase


class Info(ObjectBase):
    """
    An OpenAPI Info object, as defined in `the spec`_.

    .. _the spec: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#infoObject
    """
    __slots__ = ['title', 'description', 'termsOfService', 'contact',
                 'license', 'version']
    required_fields = ['title', 'version']

    def _parse_data(self):
        """
        Implementation of :any:`ObjectBase._parse_data`
        """
        self.contact        = self._get('contact', 'Contact')
        self.description    = self._get('description', str)
        self.license        = self._get('license', 'License')
        self.termsOfService = self._get('termsOfService', str)
        self.title          = self._get('title', str)
        self.version        = self._get('version', str)


class Contact(ObjectBase):
    """
    Contact object belonging to an Info object, as described `here`_

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#contactObject
    """
    __slots__ = ['name', 'url', 'email']
    required_fields = ['name', 'url', 'email']

    def _parse_data(self):
        """
        Implementation of :any:`ObjectBase._parse_data`
        """
        self.email = self._get('email', str)
        self.name  = self._get('name', str)
        self.url   = self._get('url', str)


class License(ObjectBase):
    """
    License object belonging to an Info object, as described `here`_

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#license-object
    """
    __slots__ = ['name', 'url']
    required_fields = ['name']

    def _parse_data(self):
        """
        Implementation of :any:`ObjectBase._parse_data`
        """
        self.name = self._get('name', str)
        self.url  = self._get('url', str)
