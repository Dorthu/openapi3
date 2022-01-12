import pathlib
import re
from typing import List, Dict, Union, Callable, Tuple

import httpx
import yarl

from aiopenapi3.v30.general import Reference
from .json import JSONReference
from . import v20
from . import v30
from . import v31
from .request import OperationIndex, HTTP_METHODS
from .errors import ReferenceResolutionError, SpecError
from .loader import Loader, NullLoader
from .plugin import Plugin, Plugins
from .base import RootBase
from .v30.paths import Operation
from .base import SchemaBase


class OpenAPI:
    @property
    def paths(self):
        return self._root.paths

    @property
    def components(self):
        return self._root.components

    @property
    def info(self):
        return self._root.info

    @property
    def openapi(self):
        return self._root.openapi

    @property
    def servers(self):
        return self._root.servers

    @classmethod
    def load_sync(
        cls, url, session_factory: Callable[[], httpx.Client] = httpx.Client, loader=None, plugins: List[Plugin] = None
    ):
        resp = session_factory().get(url)
        return cls.loads(url, resp.text, session_factory, loader, plugins)

    @classmethod
    async def load_async(
        cls,
        url,
        session_factory: Callable[[], httpx.AsyncClient] = httpx.AsyncClient,
        loader=None,
        plugins: List[Plugin] = None,
    ):
        async with session_factory() as client:
            resp = await client.get(url)
        return cls.loads(url, resp.text, session_factory, loader, plugins)

    @classmethod
    def load_file(
        cls,
        url,
        path,
        session_factory: Callable[[], httpx.AsyncClient] = httpx.AsyncClient,
        loader=None,
        plugins: List[Plugin] = None,
    ):
        assert loader
        data = loader.load(Plugins(plugins or []), path)
        return cls.loads(url, data, session_factory, loader, plugins)

    @classmethod
    def loads(
        cls,
        url,
        data,
        session_factory: Callable[[], httpx.AsyncClient] = httpx.AsyncClient,
        loader=None,
        plugins: List[Plugin] = None,
    ):
        if loader is None:
            loader = NullLoader()
        data = loader.parse(Plugins(plugins or []), pathlib.Path(url), data)
        return cls(url, data, session_factory, loader, plugins)

    def _parse_obj(self, raw_document):
        v = raw_document.get("openapi", None)
        if v:
            v = list(map(int, v.split(".")))
            if v[0] == 3:
                if v[1] == 0:
                    return v30.Root.parse_obj(raw_document)
                elif v[1] == 1:
                    return v31.Root.parse_obj(raw_document)
                else:
                    raise ValueError(f"openapi version 3.{v[1]} not supported")
            else:
                raise ValueError(f"openapi major version {v[0]} not supported")
            return

        v = raw_document.get("swagger", None)
        if v:
            v = list(map(int, v.split(".")))
            if v[0] == 2 and v[1] == 0:
                return v20.Root.parse_obj(raw_document)
            else:
                raise ValueError(f"swagger version {'.'.join(v)} not supported")
        else:
            raise ValueError("missing openapi/swagger field")

    def __init__(
        self,
        url,
        document,
        session_factory: Callable[[], Union[httpx.Client, httpx.AsyncClient]] = httpx.AsyncClient,
        loader=None,
        plugins: List[Plugin] = None,
    ):
        """
        Creates a new OpenAPI document from a loaded spec file.  This is
        overridden here because we need to specify the path in the parent
        class' constructor.

        :param document: The raw OpenAPI file loaded into python
        :type document: dct
        :param session_factory: default uses new session for each call, supply your own if required otherwise.
        :type session_factory: returns httpx.AsyncClient or http.Client
        """

        self._base_url: yarl.URL = yarl.URL(url)

        self._session_factory: Callable[[], Union[httpx.Client, httpx.AsyncClient]] = session_factory

        """
        Loader - loading referenced documents
        """
        self.loader: Loader = loader

        """
        creates the Async/Request for the protocol required
        """
        self._createRequest: Callable[["OpenAPI", str, str, "Operation"], "RequestBase"] = None

        """
        authorization informations
        e.g. {"BasicAuth": ("user","secret")}
        """
        self._security: Dict[str, Tuple[str]] = None

        """
        the related documents
        """
        self._documents: Dict[str, RootBase] = dict()

        """
        the plugin interface allows taking care of defects in description documents and implementations
        """
        self.plugins: Plugins = Plugins(plugins or [])

        document = self.plugins.document.parsed(url=url, document=document).document

        self._root = self._parse_obj(document)

        if issubclass(getattr(session_factory, "__annotations__", {}).get("return", None.__class__), httpx.Client) or (
            type(session_factory) == type and issubclass(session_factory, httpx.Client)
        ):
            if isinstance(self._root, v20.Root):
                self._createRequest = v20.Request
            elif isinstance(self._root, (v30.Root, v31.Root)):
                self._createRequest = v30.Request
            else:
                raise ValueError(self._root)
        elif issubclass(
            getattr(session_factory, "__annotations__", {}).get("return", None.__class__), httpx.AsyncClient
        ) or (type(session_factory) == type and issubclass(session_factory, httpx.AsyncClient)):
            if isinstance(self._root, v20.Root):
                self._createRequest = v20.AsyncRequest
            elif isinstance(self._root, (v30.Root, v31.Root)):
                self._createRequest = v30.AsyncRequest
            else:
                raise ValueError(self._root)
        else:
            raise ValueError("invalid return value annotation for session_factory")

        self._root._resolve_references(self)
        for i in list(self._documents.values()):
            i._resolve_references(self)

        operation_map = set()

        def test_operation(operation_id):
            if operation_id in operation_map:
                raise SpecError(f"Duplicate operationId {operation_id}", element=None)
            operation_map.add(operation_id)

        if isinstance(self._root, v20.Root):
            if self.paths:
                for path, obj in self.paths.items():
                    for m in obj.__fields_set__ & HTTP_METHODS:
                        op = getattr(obj, m)
                        _validate_parameters(op, path)
                        if op.operationId is None:
                            continue
                        formatted_operation_id = op.operationId.replace(" ", "_")
                        test_operation(formatted_operation_id)
                        for r, response in op.responses.items():
                            if isinstance(response, Reference):
                                continue
                            if isinstance(response.schema_, (v20.Schema,)):
                                response.schema_._identity = f"{path}.{m}.{r}"

        elif isinstance(self._root, (v30.Root, v31.Root)):
            if self.components:
                for name, schema in filter(lambda v: isinstance(v[1], SchemaBase), self.components.schemas.items()):
                    schema._identity = name

            if self.paths:
                for path, obj in self.paths.items():
                    for m in obj.__fields_set__ & HTTP_METHODS:
                        op = getattr(obj, m)
                        _validate_parameters(op, path)
                        if op.operationId is None:
                            continue
                        formatted_operation_id = op.operationId.replace(" ", "_")
                        test_operation(formatted_operation_id)
                        for r, response in op.responses.items():
                            if isinstance(response, Reference):
                                continue
                            for c, content in response.content.items():
                                if content.schema_ is None:
                                    continue
                                if isinstance(content.schema_, (v30.Schema,)):
                                    content.schema_._identity = f"{path}.{m}.{r}.{c}"
        else:
            raise ValueError(self._root)
        self.plugins.init.initialized(initialized=self._root)

    @property
    def url(self):
        if isinstance(self._root, v20.Root):
            r = self._base_url.with_path(self._root.basePath)
            if self._root.host:
                r = r.with_host(r)
            return r
        elif isinstance(self._root, (v30.Root, v31.Root)):
            return self._base_url.join(yarl.URL(self._root.servers[0].url))

    # public methods
    def authenticate(self, security_scheme, value):
        """
        Authenticates all subsequent requests with the given arguments.

        TODO - this should support more than just HTTP Auth
        """

        # authentication is optional and can be disabled
        if security_scheme is None:
            self._security = None
            return

        if isinstance(self._root, v20.Root):
            if security_scheme not in self._root.securityDefinitions:
                raise ValueError("{} does not accept security scheme {}".format(self.info.title, security_scheme))
        elif isinstance(self._root, (v30.Root, v31.Root)):
            if security_scheme not in self._root.components.securitySchemes:
                raise ValueError("{} does not accept security scheme {}".format(self.info.title, security_scheme))

        self._security = {security_scheme: value}

    def _load(self, i):
        data = self.loader.get(self.plugins, i)
        return self._parse_obj(data)

    @property
    def _(self):
        return OperationIndex(self)

    def resolve_jr(self, root: "Rootv30", obj, value: Reference):
        url, jp = JSONReference.split(value.ref)
        if url != "":
            url = pathlib.Path(url)
            if url not in self._documents:
                self._documents[url] = self._load(url)
            root = self._documents[url]

        try:
            return root.resolve_jp(jp)
        except ReferenceResolutionError as e:
            # add metadata to the error
            e.element = obj
            raise


def _validate_parameters(op: "Operation", path):
    """
    Ensures that all parameters for this path are valid
    """
    assert isinstance(path, str)
    allowed_path_parameters = re.findall(r"{([a-zA-Z0-9\-\._~]+)}", path)

    for c in op.parameters:
        if c.in_ == "path":
            if c.name not in allowed_path_parameters:
                raise SpecError("Parameter name not found in path: {}".format(c.name))
