import dataclasses
from typing import ForwardRef, Union, List, Optional, Dict
import json
import re

from pydantic import Field
import requests

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

from .errors import SpecError
from .object_base import ObjectBase
from .schemas import Model

from .info import Info
#from .components import Components
from .servers import Server
from .tag import Tag
from .general import Reference
from .general import ExternalDocumentation
from .schemas import Schema
from .example import Example


def _validate_parameters(op: "Operation", _path):
    """
    Ensures that all parameters for this path are valid
    """
    allowed_path_parameters = re.findall(r'{([a-zA-Z0-9\-\._~]+)}', _path[1])

    for c in op.parameters:
        if c.in_ == 'path':
            if c.name not in allowed_path_parameters:
                raise SpecError('Parameter name not found in path: {}'.format(c.name), path=_path)


class Path(ObjectBase):
    """
    A Path object, as defined `here`_.  Path objects represent URL paths that
    may be accessed by appending them to a Server

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#paths-object
    """
    delete: Optional[ForwardRef('Operation')] = Field(default=None)
    description: Optional[str] = Field(default=None)
    get: Optional[ForwardRef('Operation')] = Field(default=None)
    head: Optional[ForwardRef('Operation')] = Field(default=None)
    options: Optional[ForwardRef('Operation')] = Field(default=None)

    patch: Optional[ForwardRef('Operation')] = Field(default=None)
    post: Optional[ForwardRef('Operation')] = Field(default=None)
    put: Optional[ForwardRef('Operation')] = Field(default=None)
    servers: Optional[List[Server]] = Field(default=None)
    summary: Optional[str] = Field(default=None)
    trace: Optional[ForwardRef('Operation')] = Field(default=None)

    parameters: Optional[List[Union['Parameter', Reference]]] = Field(default_factory=list)

    def _parse_data(self):
        """
        Implementation of :any:`ObjectBase._parse_data`
        """
        # TODO - handle possible $ref
        super()._parse_data()
        if self.parameters is None:
            # this will be iterated over later
            self.parameters = []

    # def _resolve_references(self, root):
    #     """
    #     Overloaded _resolve_references to allow us to verify parameters after
    #     we've got all references settled.
    #     """
    #     super(self.__class__, self)._resolve_references(root)
    #
    #     # this will raise if parameters are invalid
    #     _validate_parameters(self)



class Parameter(ObjectBase):
    """
    A `Parameter Object`_ defines a single operation parameter.

    .. _Parameter Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#parameterObject
    """

    in_: str = Field(required=True, alias="in")  # TODO must be one of ["query","header","path","cookie"]
    name: str = Field(required=True)

    deprecated: Optional[bool] = Field(default=None)
    description: Optional[str] = Field(default=None)
    example: Optional[str] = Field(default=None)
    examples: Optional[Dict[str, Union['Example','Reference']]] = Field(default_factory=dict)
    explode: Optional[bool] = Field(default=None)
    required: Optional[bool] = Field(default=None)
    schema_: Optional[Union['Schema', 'Reference']] = Field(default=None, alias="schema")
    style: Optional[str] = Field(default=None)

    # allow empty or reserved values in Parameter data
    allowEmptyValue: Optional[bool] = Field(default=None)
    allowReserved: Optional[bool] = Field(default=None)

    @classmethod
    def can_parse(cls, dct):
        return super().can_parse(dct)

    def _parse_data(self):
#        super()._parse_data()
#        self.in_ = self._get("in", str)

        # required is required and must be True if this parameter is in the path
        if self.in_ == "path" and self.required is not True:
            err_msg = 'Parameter {} must be required since it is in the path'
            raise SpecError(err_msg.format(self.get_path()), path=self._path)

from pydantic import validator

class Operation(ObjectBase):
    """
    An Operation object as defined `here`_

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#operationObject
    """

    responses: Dict[str, Union['Response', 'Reference']] = Field(required=True)

    deprecated: Optional[bool] = Field(default=None)
    description: Optional[str] = Field(default=None)
    externalDocs: Optional[ForwardRef('ExternalDocumentation')] = Field(default=None)
    operationId: Optional[str] = Field(default=None)
    parameters: List[Union['Parameter', 'Reference']] = Field(default_factory=list)
    requestBody: Optional[Union['RequestBody', 'Reference']] = Field(default=None)
    security: Optional[List['SecurityRequirement']] = Field(default_factory=list)
    servers: Optional[List['Server']] = Field(default=None)
    summary: Optional[str] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)

    _root = object
    _path: str
    _method: str
    _request: object
    _session: object

    class Config:
        underscore_attrs_are_private = True

    def _parse_data(self):
        """
        Implementation of :any:`ObjectBase._parse_data`
        """
        super()._parse_data()
        # callbacks: dict TODO

        # gather all operations into the spec object
        if self.operationId is not None:
            # TODO - how to store without an operationId?
            formatted_operation_id = self.operationId.replace(" ", "_")
            self._root._register_operation(formatted_operation_id, self)

        # Store session object

#    def _resolve_references(self, root):
#        """
#        Overloaded _resolve_references to allow us to verify parameters after
#        we've got all references settled.
#        """
#        super(self.__class__, self)._resolve_references()
#
#        # this will raise if parameters are invalid
#        _validate_parameters(self)

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

            if ss.in_ == 'cookie':
                self._request.cookies ={ss.name:value}

    def _request_handle_parameters(self, parameters={}):
        # Parameters
        path_parameters = {}
        accepted_parameters = {}
        p = self.parameters + self._root.paths[self._path].parameters

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
        self._request = requests.Request(self._method)

        # Set self._request.url to base_url w/ path
        self._request.url = base_url + self._path

        self._session = requests.Session()


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

        if expected_response.content is None:
            return None

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
            return expected_media.schema_.model(result.json())
        else:
            raise NotImplementedError()



class SecurityRequirement(ObjectBase):
    """
    A `SecurityRequirement`_ object describes security schemes for API access.

    .. _SecurityRequirement: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#securityRequirementObject
    """

    name: Optional[str] = Field(default=None)
    types: Optional[List[str]] = Field(default=None)

    def _parse_data(self):
        """
        """
        # usually these only ever have one key
        if len(self._raw_element.keys()) == 1:
            self.name  = [c for c in self._raw_element.keys()][0]
            self.types = self._get(self.name, List[str])
        elif len(self._raw_element.keys()) == 0:
            # optional
            self.name = self.types = None


    @classmethod
    def can_parse(cls, dct):
        """
        This needs to ignore can_parse since the objects it's parsing are not
        regular - they must always have only one key though or be empty for Optional Security Requirements
        """
        return len(dct.keys()) == 1 and isinstance([c for c in dct.values()][0], list) or len(dct.keys()) == 0

    def __getstate__(self):
        return {self.name: self.types}



class RequestBody(ObjectBase):
    """
    A `RequestBody`_ object describes a single request body.

    .. _RequestBody: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#requestBodyObject
    """

    content: Dict[str, ForwardRef('MediaType')] = Field(default_factory=dict)
    description: Optional[str] = Field(default=None)
    required: Optional[bool] = Field(default=None)



class MediaType(ObjectBase):
    """
    A `MediaType`_ object provides schema and examples for the media type identified
    by its key.  These are used in a RequestBody object.

    .. _MediaType: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#mediaTypeObject
    """

    schema_: Optional[Union['Schema', 'Reference']] = Field(required=True, alias="schema")
    example: Optional[str] = Field(default=None)  # 'any' type
    examples: Optional[Dict[str, Union['Example', 'Reference']]] = Field(default_factory=dict)
    encoding: Optional[Dict[str, str]] = Field(default_factory=dict)



class Response(ObjectBase):
    """
    A `Response Object`_ describes a single response from an API Operation,
    including design-time, static links to operations based on the response.

    .. _Response Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#response-object
    """

    description: str = Field(required=True)
    content: Optional[Dict[str, ForwardRef('MediaType')]] = Field(default_factory=dict)
    links: Optional[Dict[str, Union['Link', 'Reference']]] = Field(default_factory=dict)


from pydantic import root_validator, validator

class Link(ObjectBase):
    """
    A `Link Object`_ describes a single Link from an API Operation Response to an API Operation Request

    .. _Link Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#linkObject
    """

    operationId: Optional[str] = Field(default=None)
    operationRef: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    parameters: Optional[dict] = Field(default=None)
    requestBody: Optional[dict] = Field(default=None)
    server: Optional[ForwardRef('Server')] = Field(default=None)

#    @validator("operationId", always=True)
#    def operationId_check(cls, v):
#        assert False

    @root_validator(pre=False)
    def operation_check(cls, values):
        if values["operationId"] != None and values["operationRef"] != None:
            raise SpecError("operationId and operationRef are mutually exclusive, only one of them is allowed")

        if values["operationId"] == values["operationRef"] == None:
            raise SpecError("operationId and operationRef are mutually exclusive, one of them must be specified")

        return values


Path.update_forward_refs()
Operation.update_forward_refs()
MediaType.update_forward_refs()
RequestBody.update_forward_refs()
Response.update_forward_refs()