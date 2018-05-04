from .object_base import ObjectBase

class Info(ObjectBase):
    """
    An OpenAPI Info object, as defined in `the spec`_.

    .. _the spec: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#infoObject
    """
    __slots__ = ['title','description','termsOfService','contact','license','version']

    def __init__(self, path, raw_element):
        """
        """
        super().__init__(path, raw_element)

        self._required_fields('title', 'version')

        self.title = self._get('title', str)
        self.description = self._get('description', str)
        self.termsOfService = self._get('termsOfService', str)
        self.contact = self._get('contact', 'Contact')
        self.license = self._get('license', 'License')
        self.version = self._get('version', str)

class Contact(ObjectBase):
    """
    Contact object belonging to an Info object, as described `here`_

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#contactObject
    """
    __slots__ = ['name','url','email']

    def __init__(self, path, raw_element):
        super().__init__(path, raw_element)

        self.name = self._get('name', str)
        self.url = self._get('url', str)
        self.email = self._get('email', str)

class License(ObjectBase):
    """
    License object belonging to an Info object, as described `here`_

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#license-object
    """
    __slots__ = ['name','url']

    def __init__(self, path, raw_element):
        super().__init__(path, raw_element)

        self._required_fields('name')

        self.name = self._get('name', str)
        self.url = self._get('url', str)
