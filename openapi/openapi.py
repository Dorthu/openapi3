from .object_base import ObjectBase

class OpenAPI(ObjectBase):
    """
    This class represents the root of the OpenAPI schema document, as defined
    in `the spec`_

    .. _the spec: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#openapi-object
    """
    __slots__ = ['openapi','info','servers','paths','components','security','tags','externalDocs']

    def __init__(self, raw_document):
        """
        Creates a new OpenAPI document from a loaded spec file

        :param raw_document: The raw OpenAPI file loaded into python
        :type raw_document: dct
        """
        super().__init__([], raw_document) # as the document root, we have no path

        self._required_fields('openapi', 'info', 'paths')

        self.openapi = self._get('openapi', str)
        self.info = self._get('info', 'Info')
        self.servers = self._get('servers')
        self.paths = self._get('paths')
        self.components = self._get('components')
        self.security = self._get('security')
        self.tags = self._get('tags')
        self.externalDocs = self._get('externalDocs')
