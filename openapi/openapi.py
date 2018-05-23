from typing import List

from .object_base import ObjectBase, Map
from .errors import ReferenceResolutionError

class OpenAPI(ObjectBase):
    """
    This class represents the root of the OpenAPI schema document, as defined
    in `the spec`_

    .. _the spec: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#openapi-object
    """
    __slots__ = ['openapi','info','servers','paths','components','security','tags',
                 'externalDocs','_operation_map','_security']
    required_fields: List[str] = ['openapi','info','paths']

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

    def resolve_path(self, path):
        """
        Given a $ref path, follows the document tree and returns the given attribute.

        :param path: The path down the spec tree to follow
        :type path: list[str]

        :returns: The node requested
        :rtype: ObjectBase
        :raises ValueError: if the given path is not valid
        """
        node = self

        for part in path:
            if isinstance(node, Map):
                if part not in node:
                    raise ReferenceResolutionError(
                        'Invalid path {} in Reference'.format(path))
                node = node.get(part)
            else:
                if not hasattr(node, part):
                    raise ReferenceResolutionError('Invalid path {} in Reference'.format(path))
                node = getattr(node, part)

        return node

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

        # now that we've parsed _all_ the data, resolve all references
        self._resolve_references()

    def _get_callable(self, operation):
        """
        A helper function to create OperationCallable objects for __getattribute__,
        pre-initialized with the required values from this object.

        :param operation: The Operation the callable should call
        :type operation: callable (Operation.request)

        :returns: The callable that executes this operation with this object's
                  configuration.
        :rtype: OperationCallable
        """
        base_url = self.servers[0].url

        return OperationCallable(operation, base_url, self._security)

    def __getattribute__(self, attr):
        """
        Extended __getattribute__ function to allow resolving dynamic function
        names.  The purpose of this is to call syntax like this::

           spec = OpenAPI(raw_spec)
           spec.call_operationId()

        This method will intercept the dot notation above (spec.call_operationId)
        and look up the requested operation, returning a callable object that
        will then immediately be called by the parenthesis.

        :param attr: The attribute we're retrieving
        :type attr: str

        :returns: The attribute requested
        :rtype: any
        :raises AttributeError: if the requested attribute does not exist
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
    """
    This class is returned by instances of the OpenAPI class when members
    formatted like call_operationId are accessed, and a valid Operation is
    found, and allows calling the operation directly from the OpenAPI object
    with the configured values included.  This class is not intended to be used
    directly.
    """
    def __init__(self, operation, base_url, security):
        self.operation = operation
        self.base_url = base_url
        self.security = security

    def __call__(self, *args, **kwargs):
        return self.operation(self.base_url, *args, security=self.security,
                              **kwargs)
