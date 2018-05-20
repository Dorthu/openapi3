from .object_base import ObjectBase, Map

class OpenAPI(ObjectBase):
    """
    This class represents the root of the OpenAPI schema document, as defined
    in `the spec`_

    .. _the spec: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#openapi-object
    """
    __slots__ = ['openapi','info','servers','paths','components','security','tags',
                 'externalDocs','_operation_map','_security']
    required_fields=['openapi','info','paths']

    def __init__(self, raw_document):
        """
        Creates a new OpenAPI document from a loaded spec file.  This is
        overridden here because we need to specify the path in the parent
        class' constructor.

        :param raw_document: The raw OpenAPI file loaded into python
        :type raw_document: dct
        """
        super().__init__([], raw_document, self) # as the document root, we have no path

    # public methods
    def authenticte(self, security_scheme, value):
        """
        Authenticates all subsequent requests with the given arguments.

        TODO - this should support more than just HTTP Auth
        """
        if not security_scheme in self.components.securitySchemes:
            raise ValueError('{} does not accept security scheme {}'.format(
                self.info.title, security_scheme))

        self._security = {security_scheme: value}

    # private methods
    def _parse_data(self):
        """
        Implementation of :any:`ObjectBase._parse_data`
        """
        self._operation_map = {}

        self.openapi = self._get('openapi', str)
        self.info = self._get('info', 'Info')
        self.servers = self._get('servers', ['Server'], is_list=True)
        self.paths = self._get('paths', ['Path'], is_map=True)
        self.components = self._get('components', ['Components'])
        self.security = self._get('security', dict)
        self.tags = self._get('tags', dict)
        self.externalDocs = self._get('externalDocs', dict)

    def _get_callable(self, operation):
        """
        TODO - explain this
        """
        base_url = self.servers[0].url

        return OperationCallable(operation, base_url, self._security)

    def __getattribute__(self, attr):
        """
        TODO - describe what this does
        """
        if attr.startswith('call_'):
            _, operationId = attr.split('_', 1)
            if operationId in self._operation_map:
                return self._get_callable(self._operation_map[operationId].request)
            else:
                raise AttributeError('{} has no operation {}'.format(
                    self.info.title, operationId))

        return object.__getattribute__(self, attr)


class OperationCallable:
    def __init__(self, operation, base_url, security):
        self.operation = operation
        self.base_url = base_url
        self.security = security

    def __call__(self, *args, **kwargs):
        return self.operation(self.base_url, *args, security=self.security,
                              **kwargs)
