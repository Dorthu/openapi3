import json
import re
from typing import Union, List, Optional, Dict, Any

import requests
from pydantic import Field, BaseModel, root_validator

from .errors import SpecError
from .object_base import ObjectBase, ObjectExtended

from .servers import Server
from .general import Reference
from .general import ExternalDocumentation
from .schemas import Schema
from .example import Example


def _validate_parameters(op: "Operation", path):
    """
    Ensures that all parameters for this path are valid
    """
    assert isinstance(path, str)
    allowed_path_parameters = re.findall(r'{([a-zA-Z0-9\-\._~]+)}', path)

    for c in op.parameters:
        if c.in_ == 'path':
            if c.name not in allowed_path_parameters:
                raise SpecError('Parameter name not found in path: {}'.format(c.name))


class ParameterBase(ObjectExtended):
    """
    A `Parameter Object`_ defines a single operation parameter.

    .. _Parameter Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#parameterObject
    """

    description: Optional[str] = Field(default=None)
    required: Optional[bool] = Field(default=None)
    deprecated: Optional[bool] = Field(default=None)
    allowEmptyValue: Optional[bool] = Field(default=None)

    style: Optional[str] = Field(default=None)
    explode: Optional[bool] = Field(default=None)
    allowReserved: Optional[bool] = Field(default=None)
    schema_: Optional[Union[Schema, Reference]] = Field(default=None, alias="schema")
    example: Optional[str] = Field(default=None)
    examples: Optional[Dict[str, Union['Example',Reference]]] = Field(default_factory=dict)

    content: Optional[Dict[str, "MediaType"]]

    @root_validator
    def validate_ParameterBase(cls, values):
#        if values["in_"] ==
#        if self.in_ == "path" and self.required is not True:
#            err_msg = 'Parameter {} must be required since it is in the path'
#            raise SpecError(err_msg.format(self.get_path()), path=self._path)
        return values


class Parameter(ParameterBase):
    in_: str = Field(required=True, alias="in")  # TODO must be one of ["query","header","path","cookie"]
    name: str = Field(required=True)


class SecurityRequirement(BaseModel):
    """
    A `SecurityRequirement`_ object describes security schemes for API access.

    .. _SecurityRequirement: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#securityRequirementObject
    """
    __root__: Dict[str, List[str]]

    @root_validator
    def validate_SecurityRequirement(cls, values):
        root = values.get("__root__", {})
        if not (len(root.keys()) == 1 and isinstance([c for c in root.values()][0], list) or len(root.keys()) == 0):
            raise ValueError(root)
        return values


    @property
    def name(self):
        if len(self.__root__.keys()):
            return list(self.__root__.keys())[0]
        return None

    @property
    def types(self):
        if self.name:
            return self.__root__[self.name]
        return None


class Header(ParameterBase):
    """

    .. _HeaderObject: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#headerObject
    """


class Encoding(ObjectExtended):
    """
    A single encoding definition applied to a single schema property.

    .. _Encoding: https://github.com/OAI/OpeI-Specification/blob/main/versions/3.1.0.md#encodingObject
    """
    contentType: Optional[str] = Field(default=None)
    headers: Optional[Dict[str, Union[Header, Reference]]] = Field(default_factory=dict)
    style: Optional[str] = Field(default=None)
    explode: Optional[bool] = Field(default=None)
    allowReserved: Optional[bool] = Field(default=None)


class MediaType(ObjectExtended):
    """
    A `MediaType`_ object provides schema and examples for the media type identified
    by its key.  These are used in a RequestBody object.

    .. _MediaType: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#mediaTypeObject
    """

    schema_: Optional[Union[Schema, Reference]] = Field(required=True, alias="schema")
    example: Optional[Any] = Field(default=None)  # 'any' type
    examples: Optional[Dict[str, Union[Example, Reference]]] = Field(default_factory=dict)
    encoding: Optional[Dict[str, Encoding]] = Field(default_factory=dict)


class RequestBody(ObjectExtended):
    """
    A `RequestBody`_ object describes a single request body.

    .. _RequestBody: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#requestBodyObject
    """

    content: Dict[str, MediaType] = Field(default_factory=dict)
    description: Optional[str] = Field(default=None)
    required: Optional[bool] = Field(default=None)


class Link(ObjectExtended):
    """
    A `Link Object`_ describes a single Link from an API Operation Response to an API Operation Request

    .. _Link Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#linkObject
    """

    operationId: Optional[str] = Field(default=None)
    operationRef: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    parameters: Optional[dict] = Field(default=None)
    requestBody: Optional[dict] = Field(default=None)
    server: Optional[Server] = Field(default=None)

    @root_validator(pre=False)
    def validate_Link_operation(cls, values):
        if values["operationId"] != None and values["operationRef"] != None:
            raise SpecError("operationId and operationRef are mutually exclusive, only one of them is allowed")

        if values["operationId"] == values["operationRef"] == None:
            raise SpecError("operationId and operationRef are mutually exclusive, one of them must be specified")

        return values


class Response(ObjectExtended):
    """
    A `Response Object`_ describes a single response from an API Operation,
    including design-time, static links to operations based on the response.

    .. _Response Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#response-object
    """

    description: str = Field(required=True)
    headers: Optional[Dict[str, Union[Header, Reference]]] = Field(default_factory=dict)
    content: Optional[Dict[str, MediaType]] = Field(default_factory=dict)
    links: Optional[Dict[str, Union[Link, Reference]]] = Field(default_factory=dict)


class Operation(ObjectExtended):
    """
    An Operation object as defined `here`_

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#operationObject
    """

    responses: Dict[str, Union[Response, Reference]] = Field(required=True)

    deprecated: Optional[bool] = Field(default=None)
    description: Optional[str] = Field(default=None)
    externalDocs: Optional[ExternalDocumentation] = Field(default=None)
    operationId: Optional[str] = Field(default=None)
    parameters: List[Union[Parameter, Reference]] = Field(default_factory=list)
    requestBody: Optional[Union[RequestBody, Reference]] = Field(default=None)
    security: Optional[List[SecurityRequirement]] = Field(default_factory=list)
    servers: Optional[List[Server]] = Field(default=None)
    summary: Optional[str] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)

    callbacks: Optional[Dict[str, "Callback"]] = Field(default_factory=dict)

    """
    The OpenAPISpec this is part of
    """
    _spec: "OpenAPISpec"

    _path: str
    _method: str
    _request: object
    _session: object

    class Config:
        underscore_attrs_are_private = True


    def _request_handle_secschemes(self, security_requirement, value):
        ss = self._spec.components.securitySchemes[security_requirement.name]

        if ss.type == 'http' and ss.scheme_ == 'basic':
            self._request.auth = requests.auth.HTTPBasicAuth(*value)

        if ss.type == 'http' and ss.scheme_ == 'digest':
            self._request.auth = requests.auth.HTTPDigestAuth(*value)

        if ss.type == 'http' and ss.scheme_ == 'bearer':
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
        p = self.parameters + self._spec.paths[self._path].parameters

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
            if isinstance(data, (dict, list)):
                body = json.dumps(data)

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
        self._request = requests.Request(self._method, cookies={})

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
                raise ValueError(f"No security requirement satisfied (accepts {', '.join(self.security.keys()) })")

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

        if len(expected_response.content) == 0:
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


class Path(ObjectExtended):
    """
    A Path object, as defined `here`_.  Path objects represent URL paths that
    may be accessed by appending them to a Server

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#paths-object
    """
    ref: Optional[str] = Field(default=None, alias="$ref")
    summary: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    get: Optional[Operation] = Field(default=None)
    put: Optional[Operation] = Field(default=None)
    post: Optional[Operation] = Field(default=None)
    delete: Optional[Operation] = Field(default=None)
    options: Optional[Operation] = Field(default=None)
    head: Optional[Operation] = Field(default=None)
    patch: Optional[Operation] = Field(default=None)
    trace: Optional[Operation] = Field(default=None)
    servers: Optional[List[Server]] = Field(default=None)
    parameters: Optional[List[Union[Parameter, Reference]]] = Field(default_factory=list)


class Callback(ObjectBase):
    """
    A map of possible out-of band callbacks related to the parent operation.

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.1.md#callbackObject

    This object MAY be extended with Specification Extensions.
    """
    __root__: Dict[str, Union[str, Path]]

Operation.update_forward_refs()
Parameter.update_forward_refs()
Header.update_forward_refs()