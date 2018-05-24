import json
import requests
from urllib.parse import urlencode # TODO - this will break in python2

from .errors import SpecError
from .object_base import ObjectBase
from .schemas import Model

class Path(ObjectBase):
    """
    A Path object, as defined `here`_.  Path objects represent URL paths that
    may be accessed by appending them to a Server

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#paths-object
    """
    __slots__ = ['summary','description','get','put','post','delete','options',
                 'head', 'patch','trace','servers','parameters']

    def _parse_data(self):
        """
        Implementation of :any:`ObjectBase._parse_data`
        """
        # TODO - handle possible $ref
        self.summary = self._get("summary", str)
        self.description = self._get("description", str)
        self.get = self._get("get", 'Operation')
        self.put = self._get("put", 'Operation')
        self.post = self._get("post", 'Operation')
        self.delete = self._get("delete", 'Operation')
        self.options = self._get("options", 'Operation')
        self.head = self._get("head", 'Operation')
        self.patch = self._get("patch", 'Operation')
        self.trace = self._get("trace", 'Operation')
        self.servers = self._get("servers", ['Server'], is_list=True)
        self.parameters = self._get("parameters", ['Parameter','Reference'], is_list=True)

        if self.parameters is None:
            # this will be iterated over later
            self.parameters = []


class Parameter(ObjectBase):
    """
    A `Parameter Object`_ defines a single operation parameter.

    .. _Parameter Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#parameterObject
    """
    __slots__ = ['name','in','in_','description','required','deprecated',
                 'allowEmptyValue','style','explode','allowReserved','schema',
                 'example','examples']
    required_fields = ['name','in']


    def _parse_data(self):
        self.name = self._get('name', str)
        self.in_ = self._get('in', str) # TODO must be one of ["query","header","path","cookie"]
        self.description = self._get('description', str)
        self.required = self._get('required', bool)
        self.deprecated = self._get('deprecated', bool)
        self.allowEmptyValue = self._get('allowEmptyValue', bool)

        # TODO this is an either-or with content - see docs
        self.style = self._get('style', str)
        self.explode = self._get('explode', bool)
        self.allowReserved = self._get('allowReserved', bool)
        self.schema = self._get('schema', [dict,'Reference'])#['Schema','Reference'])
        self.example = self._get('example', str)
        self.examples = self._get('examples', dict) # Map[str: ['Example','Reference']]

        # required is required and must be True if this parameter is in the path
        if self.in_ == "path" and self.required != True:
            raise SpecError("Parameter {} must be required since it is in the path".format(
                self.get_path()))

class Operation(ObjectBase):
    """
    An Operation object as defined `here`_

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#operationObject
    """
    __slots__ = ['tags','summary','description','externalDocs','operationId',
                 'parameters','requestBody','responses','callbacks','deprecated',
                 'security','servers']
    required_fields = ['responses']

    def _parse_data(self):
        """
        Implementation of :any:`ObjectBase._parse_data`
        """
        self.tags = self._get('tags', list)
        self.summary = self._get('summary', str)
        self.description = self._get('description', str)
        self.externalDocs = self._get('externalDocs', 'ExternalDocumentation')
        self.operationId = self._get('operationId', str)
        self.parameters = self._get('parameters', ['Parameter','Reference'], is_list=True)
        self.requestBody = self._get('requestBody', ['RequestBody','Reference'])
        self.responses = self._get('responses', ['Response','Reference'], is_map=True)
        #self.callbacks = self._get('callbacks', dict) TODO
        self.deprecated = self._get('deprecated', bool)
        self.security = self._get('security',['SecurityRequirement'], is_list=True)
        self.servers = self._get('servers', ['Server'], is_list=True)
        raw_servers = self._get('servers', list)

        # gather all operations into the spec object
        if self.operationId is not None:
            # TODO - how to store without an operationId?
            self._root._operation_map[self.operationId] = self

        # TODO - maybe make this generic
        if self.security is None:
            self.security = []
        if self.parameters is None:
            self.parameters = []

    def request(self, base_url, security={}, data=None, parameters={}):
        """
        Sends an HTTP request as described by this Path

        :param base_url: The URL to append this operation's path to when making
                         the call.
        :type base_url: str
        :param security: The security scheme to use, and the values it needs to
                         process successfully.
        :type secuirity: dict{str: str}
        :param data: The request body to send.
        :type data: any, should match content/type
        """
        request_method = self.path[-1] # get the request method

        method = getattr(requests, request_method) # call this

        headers = {}
        body = None
        path = self.path[-2] # TODO - this won't work for $refs
        query_params = {}

        if security and self.security:
            # find a security requirement - according to `the spec`_, only one
            # of these needs to be satisfied to authorize a request (we'll be
            # using the first
            # .. _the spec: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#security-requirement-object
            for scheme, value in security.items():
                security_requirement = None
                for r in self.security:
                    if r.name == scheme:
                        security_requirement = r
                        break

                if security_requirement is not None:
                    break # we found one

            if security_requirement is None:
                raise ValueError("No security requirement satisfied (accepts {})".format(
                    ', '.join(self.security.keys())))

            security_scheme = self._root.components.securitySchemes[security_requirement.name]

            if security_scheme.type == 'http':
                if security_scheme.scheme == 'basic':
                    raise NotImplementedError()
                elif security_scheme.scheme == 'bearer':
                    header_format = security_scheme.bearerFormat or 'Bearer {}'
                    headers['Authorization'] = header_format.format(value)
                elif security_scheme.scheme == 'digest':
                    raise NotImplementedError()
                else:
                    # TODO https://www.iana.org/assignments/http-authschemes/http-authschemes.xhtml
                    # defines many more authentication schemes that OpenAPI says it supports
                    raise NotImplementedError()
            elif security_scheme.type == 'apiKey':
                raise NotImplementedError()
            elif security_scheme.type == 'oauth2':
                raise NotImplementedError()
            elif security_scheme.type == 'openIdConnect':
                raise NotImplementedError()

        if self.requestBody:
            if self.requestBody.required and data is None:
                raise ValueError("Request Body is required but none was provided.")

            if 'application/json' in self.requestBody.content:
                if isinstance(data, dict):
                    body = json.dumps(data)
                elif issubclass(type(data), Model):
                    converter = lambda c: dict(c) # serialize models as dicts
                    body = json.dumps({k: v for k, v in data if v is not None},
                                       default=converter)
                headers['Content-Type'] = 'application/json'
            else:
                raise NotImplementedError()

        accepted_parameters = {p.name: p for p in self.parameters} # TODO better copy
        # TODO - make this work with $refs - can operations be $refs?
        accepted_parameters.update({p.name: p for p in self._root.paths[self.path[-2]].parameters})

        # TODO - this should error if it got a bad parameter
        for name, spec in accepted_parameters.items():
            if spec.required and not name in parameters:
                raise ValueError('Required parameter {} not provided'.format(
                    name))

            if name in parameters:
                value = parameters[name]

                if spec.in_ == 'path':
                    # the path's name should match the parameter name, so this
                    # should work in all cases
                    path = path.format(**{name: value})
                elif spec.in_ == 'query':
                    query_params[name] = value
                    # TODO - make sure this is good enough
                elif spec.in_ == 'header':
                    raise NotImplementedError()
                elif spec.in_ == 'cookie':
                    raise NotImplementedError()

        final_url = base_url + path + "?" +  urlencode(query_params)

        result =  method(final_url, headers=headers, data=body)

        # examine result to see how we should handle it
        # TODO - this should all be refactored into more functions, this is
        # getting too long
        status_code = str(result.status_code) # spec enforces these are strings
        expected_response = None

        # find the response model we received
        if status_code in self.responses:
            expected_response = self.responses[status_code]
        elif 'default' in self.responses:
            expected_response = self.responses['default']
        else:
            # TODO - custom exception class that has the response object in it
            raise RuntimeError('Unexpected response {} from {} (expected one of {}, '
                               'no default is defined)'.format(
                                   result.status_code, self.operationId,
                                   ','.join(self.responses.keys())))

        content_type = result.headers['Content-Type']
        expected_media = expected_response.content.get(content_type, None)

        if expected_media is None and '/' in content_type:
            # accept media type ranges in the spec - the most specific matching
            # type should always be chosen, but if we don't have a match here
            # a generic range should be accepted if one if provided
            # https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#response-object
            generic_type = content_type.split('/')[0]+'/*'
            expected_media = expected_response.content.get(generic_type, None)

        if expected_media is None:
            raise RuntimeError('Unexpected content type {} returned for operation {} '
                               '(expected one of {})'.format(
                                   result.headers['Content-Type'], self.operationId,
                                   ','.join(expected_response.content.keys())))

        response_data = None

        if content_type.lower() == 'application/json':
            return expected_media.schema.model(result.json())
        else:
            raise NotImplementedError()


class SecurityRequirement(ObjectBase):
    """
    """
    ___slots__ = ['name','types']
    required_fields=[]

    def _parse_data(self):
        """
        """
        # these only ever have one key
        self.name = [c for c in self.raw_element.keys()][0]
        self.types = self._get(self.name, str, is_list=True)

    @classmethod
    def can_parse(cls, dct):
        """
        This needs to ignore can_parse since the objects it's parsing are not
        regular - they must always have only one key though.
        """
        return len(dct.keys()) == 1 and isinstance([c for c in dct.values()][0], list)

    def __dict__(self):
        return {self.name: self.types}


class RequestBody(ObjectBase):
    """
    A `RequestBody`_ object describes a single request body.

    .. _RequestBody: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#requestBodyObject
    """
    __slots__ = ['description','content','required']
    required_fields = ['content']

    def _parse_data(self):
        """
        Implementation of :any:`ObjectBase._parse_data`
        """
        self.description = self._get('description', str)
        self.content = self._get('content', ['MediaType'], is_map=True)
        raw_content = self._get('content', dict)
        self.required = self._get('required', bool)


class MediaType(ObjectBase):
    """
    A `MediaType`_ object provides schema and examples for the media type identified
    by its key.  These are used in a RequestBody object.

    .. _MediaType: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#mediaTypeObject
    """
    __slots__ = ['schema','example','examples','encoding']
    required_fields = []

    def _parse_data(self):
        """
        Implementation of :any:`ObjectBase._parse_data`
        """
        self.schema = self._get('schema', ['Schema', 'Reference'])
        self.example = self._get('example', str)# 'any' type
        self.examples = self._get('examples', ['Reference'], is_map=True)# ['Example','Reference']
        self.encoding = self._get('encoding', dict) # Map['Encoding']


class Response(ObjectBase):
    """
    A `Response Object`_ describes a single response from an API Operation,
    including design-time, static links to operations based on the response.

    .. _Response Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#response-object
    """
    __slots__ = ['description','headers','content','links']
    required_fields = ['description']

    def _parse_data(self):
        """
        Implementation of :any:`ObjectBase._parse_data`
        """
        self.description = self._get('description', str)
        raw_headers = self._get('headers', dict)
        self.content = self._get('content', ['MediaType'], is_map=True)
        raw_content = self._get('content', dict)
        raw_links = self._get('links', dict)

        # TODO - raw_headers and raw_links
