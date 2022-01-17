from typing import Dict
import httpx
import pydantic
import yarl

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


class RequestBase:
    def __init__(self, api: "OpenAPI", method: str, path: str, operation: "Operation"):
        self.api = api
        self.root = api._root
        self.method = method
        self.path = path
        self.operation = operation
        self.req: RequestParameter = RequestParameter(self.path)

    def __call__(self, *args, **kwargs):
        return self.request(*args, **kwargs)

    def _factory_args(self):
        return {"auth": self.req.auth, "headers": {"user-agent": f"aiopenapi3/{__version__}"}}

    def request(self, data=None, parameters=None):
        """
        Sends an HTTP request as described by this Path

        :param data: The request body to send.
        :type data: any, should match content/type
        :param parameters: The parameters used to create the path
        :type parameters: dict{str: str}
        """
        self._prepare(data, parameters)
        with self.api._session_factory(**self._factory_args()) as session:
            req = self._build_req(session)
            result = session.send(req)
        return self._process(result)


class AsyncRequestBase(RequestBase):
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
            pi: "PathItem"
            for path, pi in spec.paths.items():
                op: "Operation"
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
        self._api: "OpenAPI" = api
        self._root: "RootBase" = api._root

        self._operations: Dict[str, "Operation"] = dict()

        for path, pi in self._root.paths.items():
            op: "Operation"
            for method in pi.__fields_set__ & HTTP_METHODS:
                op = getattr(pi, method)
                if op.operationId is None:
                    continue
                self._operations[op.operationId.replace(" ", "_")] = (method, path, op)

    def __getattr__(self, item):
        (method, path, op) = self._operations[item]
        return self._api._createRequest(self._api, method, path, op)

    def __iter__(self):
        return self.Iter(self._root)
