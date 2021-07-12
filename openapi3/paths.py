import json
import re
import requests

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

from .errors import SpecError
from .object_base import ObjectBase
from .schemas import Model


def _validate_parameters(instance):
    """
    Ensures that all parameters for this path are valid
    """
    allowed_path_parameters = re.findall(r'{([a-zA-Z0-9\-\._~]+)}', instance.path[1])

    for c in instance.parameters:
        if c.in_ == 'path':
            if c.name not in allowed_path_parameters:
                raise SpecError('Parameter name not found in path: {}'.format(c.name), path=instance.path)


class Path(ObjectBase):
    """
    A Path object, as defined `here`_.  Path objects represent URL paths that
    may be accessed by appending them to a Server

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#paths-object
    """
    __slots__ = ['summary', 'description', 'get', 'put', 'post', 'delete',
                 'options', 'head', 'patch', 'trace', 'servers', 'parameters']

    def _parse_data(self):
        """
        Implementation of :any:`ObjectBase._parse_data`
        """
        # TODO - handle possible $ref
        self.delete      = self._get('delete', 'Operation')
        self.description = self._get('description', str)
        self.get         = self._get('get', 'Operation')
        self.head        = self._get('head', 'Operation')
        self.options     = self._get('options', 'Operation')
        self.parameters  = self._get('parameters', ['Parameter', 'Reference'], is_list=True)
        self.patch       = self._get('patch', 'Operation')
        self.post        = self._get('post', 'Operation')
        self.put         = self._get('put', 'Operation')
        self.servers     = self._get('servers', ['Server'], is_list=True)
        self.summary     = self._get('summary', str)
        self.trace       = self._get('trace', 'Operation')

        if self.parameters is None:
            # this will be iterated over later
            self.parameters = []

    def _resolve_references(self):
        """
        Overloaded _resolve_references to allow us to verify parameters after
        we've got all references settled.
        """
        super(__class__, self)._resolve_references()

        # this will raise if parameters are invalid
        _validate_parameters(self)


class Parameter(ObjectBase):
    """
    A `Parameter Object`_ defines a single operation parameter.

    .. _Parameter Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#parameterObject
    """
    __slots__ = ['name', 'in', 'in_', 'description', 'required', 'deprecated',
                 'allowEmptyValue', 'style', 'explode', 'allowReserved',
                 'schema', 'example', 'examples']
    required_fields = ['name', 'in']

    def _parse_data(self):
        self.deprecated  = self._get('deprecated', bool)
        self.description = self._get('description', str)
        self.example     = self._get('example', str)
        self.examples    = self._get('examples', dict)  # Map[str: ['Example','Reference']]
        self.explode     = self._get('explode', bool)
        self.in_         = self._get('in', str)  # TODO must be one of ["query","header","path","cookie"]
        self.name        = self._get('name', str)
        self.required    = self._get('required', bool)
        self.schema      = self._get('schema', ['Schema', 'Reference'])
        self.style       = self._get('style', str)

        # allow empty or reserved values in Parameter data
        self.allowEmptyValue = self._get('allowEmptyValue', bool)
        self.allowReserved   = self._get('allowReserved', bool)

        # required is required and must be True if this parameter is in the path
        if self.in_ == "path" and self.required is not True:
            err_msg = 'Parameter {} must be required since it is in the path'
            raise SpecError(err_msg.format(self.get_path()), path=self.path)


class Operation(ObjectBase):
    """
    An Operation object as defined `here`_

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#operationObject
    """
    __slots__ = ['tags', 'summary', 'description', 'externalDocs', 'security',
                 'operationId', 'parameters', 'requestBody', 'responses',
                 'callbacks', 'deprecated', 'servers', '_session', '_request']
    required_fields = ['responses']

    def _parse_data(self):
        """
        Implementation of :any:`ObjectBase._parse_data`
        """
        raw_servers       = self._get('servers', list)
        self.deprecated   = self._get('deprecated', bool)
        self.description  = self._get('description', str)
        self.externalDocs = self._get('externalDocs', 'ExternalDocumentation')
        self.operationId  = self._get('operationId', str)
        self.parameters   = self._get('parameters', ['Parameter', 'Reference'], is_list=True)
        self.requestBody  = self._get('requestBody', ['RequestBody', 'Reference'])
        self.responses    = self._get('responses', ['Response', 'Reference'], is_map=True)
        self.security     = self._get('security', ['SecurityRequirement'], is_list=True)
        self.servers      = self._get('servers', ['Server'], is_list=True)
        self.summary      = self._get('summary', str)
        self.tags         = self._get('tags', list)
        raw_servers       = self._get('servers', list)
        # self.callbacks  = self._get('callbacks', dict) TODO

        # default parameters to an empty list for processing later
        if self.parameters is None:
            self.parameters = []

        # gather all operations into the spec object
        if self.operationId is not None:
            # TODO - how to store without an operationId?
            formatted_operation_id = self.operationId.replace(" ", "_")
            self._root._register_operation(formatted_operation_id, self)

        # TODO - maybe make this generic
        if self.security is None:
            self.security = self._root._get('security',  ['SecurityRequirement'], is_list=True) or []

        # Store session object
        self._session = requests.Session()

        # Store request object
        self._request = requests.Request()

    def _resolve_references(self):
        """
        Overloaded _resolve_references to allow us to verify parameters after
        we've got all references settled.
        """
        super(__class__, self)._resolve_references()

        # this will raise if parameters are invalid
        _validate_parameters(self)

    def _request_handle_secschemes(self, security_requirement, value):
        ss = self._root.components.securitySchemes[security_requirement.name]

        if ss.type == 'http' and ss.scheme == 'basic':
            self._request.auth = requests.auth.HTTPBasicAuth(*value)

        if ss.type == 'http' and ss.scheme == 'digest':
            self._request.auth = requests.auth.HTTPDigestAuth(*value)

        if ss.type == 'http' and ss.scheme == 'bearer':
            header = ss.bearerFormat or 'Bearer {}'
            self._request.headers['Authorization'] = header.format(value)

        if ss.type == 'mutualTLS':
            # TLS Client certificates (mutualTLS)
            self._request.cert = value

        if ss.type == 'apiKey':
            if ss.in_ == 'query':
                # apiKey in query parameter
                self._request.params[ss.name]  = value

            if ss.in_ == 'header':
                # apiKey in query header data
                self._request.headers[ss.name] = value

    def _request_handle_parameters(self, parameters={}):
        # Parameters
        path_parameters = {}
        accepted_parameters = {}
        p = self.parameters + self._root.paths[self.path[-2]].parameters

        for _ in list(p):
            # TODO - make this work with $refs - can operations be $refs?
            accepted_parameters.update({_.name: _})

        for name, spec in accepted_parameters.items():
            try:
                value = parameters[name]
            except KeyError:
                if spec.required and name not in parameters:
                    err_msg = 'Required parameter {} not provided'.format(name)
                    raise ValueError(err_msg)

                continue

            if spec.in_ == 'path':
                # The string method `format` is incapable of partial updates,
                # as such we need to collect all the path parameters before
                # applying them to the format string.
                path_parameters[name] = value

            if spec.in_ == 'query':
                self._request.params[name]  = value

            if spec.in_ == 'header':
                self._request.headers[name] = value

            if spec.in_ == 'cookie':
                self._request.cookies[name] = value

        self._request.url = self._request.url.format(**path_parameters)

    def _request_handle_body(self, data):
        if 'application/json' in self.requestBody.content:
            if isinstance(data, dict) or isinstance(data, list):
                body = json.dumps(data)

            if issubclass(type(data), Model):
                # serialize models as dicts
                converter = lambda c: dict(c)
                data_dict = {k: v for k, v in data if v is not None}

                body = json.dumps(data_dict, default=converter)

            self._request.data = body
            self._request.headers['Content-Type'] = 'application/json'
        else:
            raise NotImplementedError()

    def request(self, base_url, security={}, data=None, parameters={}, verify=True,
                session=None, raw_response=False):
        """
        Sends an HTTP request as described by this Path

        :param base_url: The URL to append this operation's path to when making
                         the call.
        :type base_url: str
        :param security: The security scheme to use, and the values it needs to
                         process successfully.
        :type security: dict{str: str}
        :param data: The request body to send.
        :type data: any, should match content/type
        :param parameters: The parameters used to create the path
        :type parameters: dict{str: str}
        :param verify: Should we do an ssl verification on the request or not,
                       In case str was provided, will use that as the CA.
        :type verify: bool/str
        :param session: a persistent request session
        :type session: None, requests.Session
        :param raw_response: If true, return the raw response instead of validating
                             and exterpolating it.
        :type raw_response: bool
        """
        # Set request method (e.g. 'GET')
        self._request = requests.Request(self.path[-1])

        # Set self._request.url to base_url w/ path
        self._request.url = base_url + self.path[-2]

        if security and self.security:
            security_requirement = None
            for scheme, value in security.items():
                security_requirement = None
                for r in self.security:
                    if r.name == scheme:
                        security_requirement = r
                        self._request_handle_secschemes(r, value)

            if security_requirement is None:
                err_msg = '''No security requirement satisfied (accepts {}) \
                          '''.format(', '.join(self.security.keys()))
                raise ValueError(err_msg)

        if self.requestBody:
            if self.requestBody.required and data is None:
                err_msg = 'Request Body is required but none was provided.'
                raise ValueError(err_msg)

            self._request_handle_body(data)

        self._request_handle_parameters(parameters)

        if session is None:
            session = self._session

        # send the prepared request
        result = session.send(self._request.prepare())

        # spec enforces these are strings
        status_code = str(result.status_code)

        # find the response model in spec we received
        expected_response = None
        if status_code in self.responses:
            expected_response = self.responses[status_code]
        elif 'default' in self.responses:
            expected_response = self.responses['default']

        if expected_response is None:
            # TODO - custom exception class that has the response object in it
            err_msg = '''Unexpected response {} from {} (expected one of {}, \
                         no default is defined'''
            err_var = result.status_code, self.operationId, ','.join(self.responses.keys())

            raise RuntimeError(err_msg.format(*err_var))

        content_type   = result.headers['Content-Type']
        expected_media = expected_response.content.get(content_type, None)

        if expected_media is None and '/' in content_type:
            # accept media type ranges in the spec. the most specific matching
            # type should always be chosen, but if we do not have a match here
            # a generic range should be accepted if one if provided
            # https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#response-object

            generic_type   = content_type.split('/')[0] + '/*'
            expected_media = expected_response.content.get(generic_type, None)

        if expected_media is None:
            err_msg = '''Unexpected Content-Type {} returned for operation {} \
                         (expected one of {})'''
            err_var = result.headers['Content-Type'], self.operationId, ','.join(expected_response.content.keys())

            raise RuntimeError(err_msg.format(*err_var))

        response_data = None

        if content_type.lower() == 'application/json':
            return expected_media.schema.model(result.json())
        else:
            raise NotImplementedError()


class SecurityRequirement(ObjectBase):
    """
    A `SecurityRequirement`_ object describes security schemes for API access.

    .. _SecurityRequirement: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#securityRequirementObject
    """
    ___slots__ = ['name', 'types']
    required_fields = []

    def _parse_data(self):
        """
        """
        # these only ever have one key
        self.name  = [c for c in self.raw_element.keys()][0]
        self.types = self._get(self.name, str, is_list=True)

    @classmethod
    def can_parse(cls, dct):
        """
        This needs to ignore can_parse since the objects it's parsing are not
        regular - they must always have only one key though.
        """
        return len(dct.keys()) == 1 and isinstance([c for c in dct.values()][0], list)

    def __getstate__(self):
        return {self.name: self.types}


class RequestBody(ObjectBase):
    """
    A `RequestBody`_ object describes a single request body.

    .. _RequestBody: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#requestBodyObject
    """
    __slots__ = ['description', 'content', 'required']
    required_fields = ['content']

    def _parse_data(self):
        """
        Implementation of :any:`ObjectBase._parse_data`
        """
        self.description = self._get('description', str)
        self.content     = self._get('content', ['MediaType'], is_map=True)
        raw_content      = self._get('content', dict)
        self.required    = self._get('required', bool)


class MediaType(ObjectBase):
    """
    A `MediaType`_ object provides schema and examples for the media type identified
    by its key.  These are used in a RequestBody object.

    .. _MediaType: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#mediaTypeObject
    """
    __slots__ = ['schema', 'example', 'examples', 'encoding']
    required_fields = []

    def _parse_data(self):
        """
        Implementation of :any:`ObjectBase._parse_data`
        """
        self.schema   = self._get('schema', ['Schema', 'Reference'])
        self.example  = self._get('example', str)  # 'any' type
        self.examples = self._get('examples', ['Example', 'Reference'], is_map=True)
        self.encoding = self._get('encoding', dict)  # Map['Encoding']


class Response(ObjectBase):
    """
    A `Response Object`_ describes a single response from an API Operation,
    including design-time, static links to operations based on the response.

    .. _Response Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#response-object
    """
    __slots__ = ['description', 'headers', 'content', 'links']
    required_fields = ['description']

    def _parse_data(self):
        """
        Implementation of :any:`ObjectBase._parse_data`
        """
        self.content     = self._get('content', ['MediaType'], is_map=True)
        self.description = self._get('description', str)
        raw_content      = self._get('content', dict)
        raw_headers      = self._get('headers', dict)
        self.links       = self._get('links', ['Link', 'Reference'], is_map=True)


class Link(ObjectBase):
    """
    A `Link Object`_ describes a single Link from an API Operation Response to an API Operation Request

    .. _Link Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#linkObject
    """
    __slots__ = ['operationId', 'operationRef', 'description', 'parameters', 'requestBody', 'server']

    def _parse_data(self):
        """
        Implementation of :any:`ObjectBase._parse_data`
        """
        self.operationId  = self._get('operationId', str)
        self.operationRef = self._get('operationRef', str)
        self.description  = self._get('description', str)
        self.parameters   = self._get('parameters', dict)
        self.requestBody  = self._get('requestBody', dict)
        self.server       = self._get('server', ['Server'])

        if self.operationId and self.operationRef:
            raise SpecError("operationId and operationRef are mutually exclusive, only one of them is allowed")
        if not (self.operationId or self.operationRef):
            raise SpecError("operationId and operationRef are mutually exclusive, one of them must be specified")
