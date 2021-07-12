import requests

from .object_base import ObjectBase, Map
from .errors import ReferenceResolutionError, SpecError


class OpenAPI(ObjectBase):
    """
    This class represents the root of the OpenAPI schema document, as defined
    in `the spec`_

    .. _the spec: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#openapi-object
    """
    __slots__ = ['openapi','info','servers','paths','components','security','tags',
                 'externalDocs','_operation_map','_security', 'validation_mode',
                 '_spec_errors', '_ssl_verify', '_session']
    required_fields=['openapi','info','paths']

    def __init__(
            self,
            raw_document,
            validate=False,
            ssl_verify=None,
            use_session=False,
            session_factory=requests.Session):
        """
        Creates a new OpenAPI document from a loaded spec file.  This is
        overridden here because we need to specify the path in the parent
        class' constructor.

        :param raw_document: The raw OpenAPI file loaded into python
        :type raw_document: dct
        :param validate: If True, don't fail on errors, but instead capture all
                         errors, continuing along the spec as best as possible,
                         and make them available when parsing is complete.
        :type validate: bool
        :param ssl_verify: Decide if to use ssl verification to the requests or not,
                           in case an str is passed, will be used as the CA.
        :type ssl_verify: bool, str, None
        :param use_session: Should we use a consistant session between API calls
        :type use_session: bool
        """
        # do this first so super().__init__ can see it
        self.validation_mode = validate

        if validate:
            self._spec_errors = []

        # as the document root, we have no path
        super(OpenAPI, self).__init__([], raw_document, self)

        self._security = {}

        self._ssl_verify = ssl_verify

        self._session = None
        if use_session:
            self._session = session_factory()

    # public methods
    def authenticte(self, security_scheme, value):
        """
        Authenticates all subsequent requests with the given arguments.

        TODO - this should support more than just HTTP Auth
        """
        if security_scheme not in self.components.securitySchemes:
            raise ValueError('{} does not accept security scheme {}'.format(
                self.info.title, security_scheme))

        self._security = {security_scheme: value}

    authenticate = authenticte

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
                if part not in node:  # pylint: disable=unsupported-membership-test
                    err_msg = 'Invalid path {} in Reference'.format(path)
                    raise ReferenceResolutionError(err_msg)
                node = node.get(part)
            else:
                if not hasattr(node, part):
                    err_msg = 'Invalid path {} in Reference'.format(path)
                    raise ReferenceResolutionError(err_msg)
                node = getattr(node, part)

        return node

    def log_spec_error(self, error):
        """
        In Validation Mode, this method is used when parsing a spec to record an
        error that was encountered, for later reporting.  This should not be used
        outside of Validation Mode.

        :param error: The error encountered.
        :type error: SpecError
        """
        if not self.validation_mode:
            raise RuntimeError('This client is not in Validation Mode, cannot '
                               'record errors!')
        self._spec_errors.append(error)

    def errors(self):
        """
        In Validation Mode, returns all errors encountered from parsing a spec.
        This should not be called if not in Validation Mode.

        :returns: The errors encountered during the parsing of this spec.
        :rtype: list[SpecError]
        """
        if not self.validation_mode:
            raise RuntimeError('This client is not in Validation Mode, cannot '
                               'return errors!')
        return self._spec_errors

    # private methods
    def _register_operation(self, operation_id, operation):
        """
        Adds an Operation to this spec's _operation_map, raising an error if the
        OperationId has already been registered.

        :param operation_id: The operation ID to register
        :type operation_id: str
        :param operation: The operation to register
        :type operation: Operation
        """
        if operation_id in self._operation_map:
            raise SpecError("Duplicate operationId {}".format(operation_id), path=operation.path)
        self._operation_map[operation_id] = operation

    def _parse_data(self):
        """
        Implementation of :any:`ObjectBase._parse_data`
        """
        self._operation_map = {}

        self.components   = self._get('components', ['Components'])
        self.externalDocs = self._get('externalDocs', dict)
        self.info         = self._get('info', 'Info')
        self.openapi      = self._get('openapi', str)
        self.paths        = self._get('paths', ['Path'], is_map=True)
        self.security     = self._get('security', ['SecurityRequirement'], is_list=True)
        self.servers      = self._get('servers', ['Server'], is_list=True)
        self.tags         = self._get('tags', ['Tag'], is_list=True)

        # now that we've parsed _all_ the data, resolve all references
        self._resolve_references()
        self._resolve_allOfs()

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

        return OperationCallable(operation, base_url, self._security, self._ssl_verify,
                                 self._session)

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
    def __init__(self, operation, base_url, security, ssl_verify, session):
        self.operation = operation
        self.base_url = base_url
        self.security = security
        self.ssl_verify = ssl_verify
        self.session = session

    def __call__(self, *args, **kwargs):
        if self.ssl_verify is not None:
            kwargs['verify'] = self.ssl_verify
        if self.session:
            kwargs['session'] = self.session
        return self.operation(self.base_url, *args, security=self.security,
                              **kwargs)
