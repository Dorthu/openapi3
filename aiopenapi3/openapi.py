import pathlib
import re
from typing import List, Dict, Union, Callable

import httpx
import yarl

from aiopenapi3.v30.general import Reference
from .json import JSONReference
from . import v30
from . import v31
from .request import OperationIndex, HTTP_METHODS
from .errors import ReferenceResolutionError, SpecError
from .loader import Loader
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
        data = Loader.parse(Plugins(plugins or []), pathlib.Path(url), data)
        return cls(url, data, session_factory, loader, plugins)

    def _parse_obj(self, raw_document):
        if not (v := raw_document.get("openapi", None)):
            raise ValueError("missing openapi field")
        v = list(map(int, v.split(".")))
        if v[0] != 3:
            raise ValueError(f"openapi major version {v[0]} not supported")
        if v[1] == 0:
            return v30.Root.parse_obj(raw_document)
        elif v[1] == 1:
            return v31.Root.parse_obj(raw_document)
        else:
            raise ValueError(f"openapi major version {v[0]} not supported")

    def __init__(
        self,
        url,
        raw_document,
        session_factory: Callable[[], Union[httpx.Client, httpx.AsyncClient]] = httpx.AsyncClient,
        loader=None,
        plugins: List[Plugin] = None,
    ):
        """
        Creates a new OpenAPI document from a loaded spec file.  This is
        overridden here because we need to specify the path in the parent
        class' constructor.

        :param raw_document: The raw OpenAPI file loaded into python
        :type raw_document: dct
        :param session_factory: default uses new session for each call, supply your own if required otherwise.
        :type session_factory: returns httpx.AsyncClient or http.Client
        """

        self._base_url: yarl.URL = yarl.URL(url)
        self.loader: Loader = loader
        self._session_factory = session_factory

        self._security: List[str] = None
        self._cached: Dict[str, RootBase] = dict()
        self.plugins = Plugins(plugins or [])

        raw_document = self.plugins.document.parsed(url=url, document=raw_document).document

        self._root = self._parse_obj(raw_document)

        self._root._resolve_references(self)
        for i in list(self._cached.values()):
            i._resolve_references(self)

        if self.components:
            for name, schema in filter(lambda v: isinstance(v[1], SchemaBase), self.components.schemas.items()):
                schema._identity = name

        if self.paths:
            operation_map = set()

            def test_operation(operation_id):
                if operation_id in operation_map:
                    raise SpecError(f"Duplicate operationId {operation_id}", element=None)
                operation_map.add(operation_id)

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

        self.plugins.init.initialized(initialized=self._root)

    @property
    def url(self):
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
            if url not in self._cached:
                self._cached[url] = self._load(url)
            root = self._cached[url]

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
