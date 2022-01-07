import json
from typing import List, Dict

import httpx
import pydantic
import yarl

from . import v30
from .base import SchemaBase, ParameterBase, HTTP_METHODS
from .version import __version__


class RequestParameter:
    def __init__(self, url: yarl.URL):
        self.url = str(url)
        self.auth = None
        self.cookies = {}
        self.path = {}
        self.params = {}
        self.content = None
        self.headers = {}


class Request:
    """
    This class is returned by instances of the OpenAPI class when members
    formatted like call_operationId are accessed, and a valid Operation is
    found, and allows calling the operation directly from the OpenAPI object
    with the configured values included.  This class is not intended to be used
    directly.
    """

    def __init__(self, api: "OpenAPI", method: str, path: str, operation: "Operation.request"):
        self.api = api
        self.spec = api._root
        self.method = method
        self.path = path
        self.operation = operation
        #        self.session:Union[httpx.Client,httpx.AsyncClient] =
        self.req: RequestParameter = RequestParameter(self.path)

    def __call__(self, *args, **kwargs):
        return self.request(*args, **kwargs)

    @property
    def security(self):
        return self.api._security

    @property
    def data(self) -> SchemaBase:
        return self.operation.requestBody.content["application/json"].schema_

    @property
    def parameters(self) -> Dict[str, ParameterBase]:
        return self.operation.parameters + self.spec.paths[self.path].parameters

    def args(self, content_type: str = "application/json"):
        op = self.operation
        parameters = op.parameters + self.spec.paths[self.path].parameters
        schema = op.requestBody.content[content_type].schema_
        return {"parameters": parameters, "data": schema}

    def return_value(self, http_status: int = 200, content_type: str = "application/json") -> SchemaBase:
        return self.operation.responses[str(http_status)].content[content_type].schema_

    def _factory_args(self):
        return {"auth": self.req.auth, "headers": {"user-agent": f"aiopenapi3/{__version__}"}}

    def _prepare_security(self):
        if self.security and self.operation.security:
            for scheme, value in self.security.items():
                for r in filter(lambda x: x.name == scheme, self.operation.security):
                    self._prepare_secschemes(r, value)
                    break
                else:
                    continue
                break
            else:
                raise ValueError(
                    f"No security requirement satisfied (accepts {', '.join(self.operation.security.keys())})"
                )

    def _prepare_secschemes(self, security_requirement: v30.SecurityRequirement, value: List[str]):
        ss = self.spec.components.securitySchemes[security_requirement.name]

        if ss.type == "http" and ss.scheme_ == "basic":
            self.req.auth = value

        if ss.type == "http" and ss.scheme_ == "digest":
            self.req.auth = httpx.DigestAuth(*value)

        if ss.type == "http" and ss.scheme_ == "bearer":
            header = ss.bearerFormat or "Bearer {}"
            self.req.headers["Authorization"] = header.format(value)

        if ss.type == "mutualTLS":
            # TLS Client certificates (mutualTLS)
            self.req.cert = value

        if ss.type == "apiKey":
            if ss.in_ == "query":
                # apiKey in query parameter
                self.req.params[ss.name] = value

            if ss.in_ == "header":
                # apiKey in query header data
                self.req.headers[ss.name] = value

            if ss.in_ == "cookie":
                self.req.cookies = {ss.name: value}

    def _prepare_parameters(self, parameters):
        # Parameters
        path_parameters = {}
        accepted_parameters = {}
        p = self.operation.parameters + self.spec.paths[self.path].parameters

        for _ in list(p):
            # TODO - make this work with $refs - can operations be $refs?
            accepted_parameters.update({_.name: _})

        for name, spec in accepted_parameters.items():
            if parameters is None or name not in parameters:
                if spec.required:
                    raise ValueError(f"Required parameter {name} not provided")
                continue

            value = parameters[name]

            if spec.in_ == "path":
                # The string method `format` is incapable of partial updates,
                # as such we need to collect all the path parameters before
                # applying them to the format string.
                path_parameters[name] = value

            if spec.in_ == "query":
                self.req.params[name] = value

            if spec.in_ == "header":
                self.req.headers[name] = value

            if spec.in_ == "cookie":
                self.req.cookies[name] = value

        self.req.url = self.req.url.format(**path_parameters)

    def _prepare_body(self, data):
        if not self.operation.requestBody:
            return

        if data is None and self.operation.requestBody.required:
            raise ValueError("Request Body is required but none was provided.")

        if "application/json" in self.operation.requestBody.content:
            if isinstance(data, (dict, list)):
                pass
            elif isinstance(data, pydantic.BaseModel):
                data = data.dict()
            else:
                raise TypeError(data)
            data = self.api.plugins.message.marshalled(
                operationId=self.operation.operationId, marshalled=data
            ).marshalled
            data = json.dumps(data)
            data = data.encode()
            data = self.api.plugins.message.sending(operationId=self.operation.operationId, sending=data).sending
            self.req.content = data
            self.req.headers["Content-Type"] = "application/json"
        else:
            raise NotImplementedError()

    def _prepare(self, data, parameters):
        self._prepare_security()
        self._prepare_parameters(parameters)
        self._prepare_body(data)

    def _build_req(self, session):
        req = session.build_request(
            self.method,
            str(self.api.url / self.req.url[1:]),
            headers=self.req.headers,
            cookies=self.req.cookies,
            params=self.req.params,
            content=self.req.content,
        )
        return req

    def _process(self, result):
        # spec enforces these are strings
        status_code = str(result.status_code)

        # find the response model in spec we received
        expected_response = None
        if status_code in self.operation.responses:
            expected_response = self.operation.responses[status_code]
        elif "default" in self.operation.responses:
            expected_response = self.operation.responses["default"]

        if expected_response is None:
            # TODO - custom exception class that has the response object in it
            options = ",".join(self.operation.responses.keys())
            raise ValueError(
                f"""Unexpected response {result.status_code} from {self.operation.operationId} (expected one of {options}), no default is defined"""
            )

        if len(expected_response.content) == 0:
            return None

        content_type = result.headers.get("Content-Type", None)
        if content_type:
            expected_media = expected_response.content.get(content_type, None)
            if expected_media is None and "/" in content_type:
                # accept media type ranges in the spec. the most specific matching
                # type should always be chosen, but if we do not have a match here
                # a generic range should be accepted if one if provided
                # https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#response-object

                generic_type = content_type.split("/")[0] + "/*"
                expected_media = expected_response.content.get(generic_type, None)
        else:
            expected_media = None

        if expected_media is None:
            options = ",".join(expected_response.content.keys())
            raise ValueError(
                f"Unexpected Content-Type {content_type} returned for operation {self.operation.operationId} \
                         (expected one of {options})"
            )

        if content_type.lower() == "application/json":
            data = result.text
            data = self.api.plugins.message.received(operationId=self.operation.operationId, received=data).received
            data = json.loads(data)
            data = self.api.plugins.message.parsed(operationId=self.operation.operationId, parsed=data).parsed
            data = expected_media.schema_.model(data)
            data = self.api.plugins.message.unmarshalled(
                operationId=self.operation.operationId, unmarshalled=data
            ).unmarshalled
            return data
        else:
            raise NotImplementedError()

    def request(self, data=None, parameters=None):
        """
        Sends an HTTP request as described by this Path

        :param data: The request body to send.
        :type data: any, should match content/type
        :param parameters: The parameters used to create the path
        :type parameters: dict{str: str}
        """

        self._prepare(data, parameters)
        session = self.api._session_factory(**self._factory_args())
        req = self._build_req(session)
        result = session.send(req)
        return self._process(result)


class AsyncRequest(Request):
    async def __call__(self, *args, **kwargs):
        return await self.request(*args, **kwargs)

    async def request(self, data=None, parameters=None):

        self._prepare(data, parameters)
        async with self.api._session_factory(**self._factory_args()) as session:
            req = self._build_req(session)
            result = await session.send(req)

        return self._process(result)


class OperationIndex:
    class Iter:
        def __init__(self, spec):
            self.operations = []
            self.r = 0
            #            pi: PathItem
            for path, pi in spec.paths.items():
                #                op: Operation
                for method in pi.__fields_set__ & HTTP_METHODS:
                    op = getattr(pi, method)
                    if op.operationId is None:
                        continue
                    self.operations.append(op.operationId)
            self.r = iter(range(len(self.operations)))

        def __iter__(self):
            return self

        def __next__(self):
            return self.operations[next(self.r)]

    def __init__(self, api):
        self._api = api
        self._spec = api._root

    def __getattr__(self, item):
        #        pi: PathItem
        for path, pi in self._spec.paths.items():
            #            op: Operation
            for method in pi.__fields_set__ & HTTP_METHODS:
                op = getattr(pi, method)
                if op.operationId != item:
                    continue
                sf = self._api._session_factory
                if issubclass(
                    getattr(sf, "__annotations__", {}).get("return", None.__class__), httpx.Client
                ) or issubclass(sf, httpx.Client):
                    return Request(self._api, method, path, op)
                if issubclass(
                    getattr(sf, "__annotations__", {}).get("return", None.__class__), httpx.AsyncClient
                ) or issubclass(sf, httpx.AsyncClient):
                    return AsyncRequest(self._api, method, path, op)

        raise ValueError(item)

    def __iter__(self):
        return self.Iter(self._spec)
