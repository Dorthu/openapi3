import sys
import gc


if sys.version_info >= (3, 9):
    import pathlib
else:
    import pathlib3x as pathlib

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
from .base import RootBase, ReferenceBase, SchemaBase
from .v30.paths import Operation


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
        self._security: Dict[str, Tuple[str]] = dict()

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

        self._init_session_factory(session_factory)
        self._init_references()
        self._init_operationindex()
        self._init_schema_types()

        self.plugins.init.initialized(initialized=self._root)

    def _init_session_factory(self, session_factory):
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

    def _init_references(self):
        self._root._resolve_references(self)
        for i in list(self._documents.values()):
            i._resolve_references(self)

    def _init_operationindex(self):
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
                                if isinstance(content.schema_, (v30.Schema, v31.Schema)):
                                    content.schema_._identity = f"{path}.{m}.{r}.{c}"

        else:
            raise ValueError(self._root)

    def _init_schema_types(self):
        """
        create & cache all the types -
        discriminated types are special,
        they need to inherit properly and have to be created when creating the parent type

        :return: None
        """
        #
        gc.collect()
        schemas = dict((id(i), i) for i in filter(lambda obj: isinstance(obj, SchemaBase), gc.get_objects()))
        init = set(schemas.keys())
        for k, i in schemas.items():
            if not i.discriminator:
                continue
            init -= frozenset(
                map(lambda x: id(x._target), filter(lambda x: isinstance(x, ReferenceBase), i.oneOf + i.anyOf))
            )

        for i in init:
            s = schemas[i]
            s.set_type()

    @property
    def url(self):
        if isinstance(self._root, v20.Root):
            base = yarl.URL(self._base_url)
            scheme = host = port = path = None

            for i in ["https", "http"]:
                if not self._root.schemes or i not in self._root.schemes:
                    continue
                scheme = i
                break
            else:
                scheme = base.scheme

            if self._root.host:
                host, _, port = self._root.host.partition(":")
            else:
                host, port = base.host, base.port

            path = self._root.basePath or base.path

            r = yarl.URL.build(scheme=scheme, host=host, port=port, path=path)
            return r
        elif isinstance(self._root, (v30.Root, v31.Root)):
            return self._base_url.join(yarl.URL(self._root.servers[0].url))

    # public methods
    def authenticate(self, *args, **kwargs):
        """

        :param args: None to remove all credentials / reset the authorizations
        :param kwargs: scheme=value
        """
        if len(args) == 1 and args[0] == None:
            self._security = dict()

        schemes = frozenset(kwargs.keys())
        if isinstance(self._root, v20.Root):
            v = schemes - frozenset(self._root.securityDefinitions)
        elif isinstance(self._root, (v30.Root, v31.Root)):
            v = schemes - frozenset(self._root.components.securitySchemes)

        if v:
            raise ValueError("{} does not accept security schemes {}".format(self.info.title, sorted(v)))

        for security_scheme, value in kwargs.items():
            if value is None:
                del self._security[security_scheme]
            else:
                self._security[security_scheme] = value

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
    allowed_path_parameters = frozenset(re.findall(r"{([a-zA-Z0-9\-\._~]+)}", path))

    path_parameters = frozenset(map(lambda x: x.name, filter(lambda c: c.in_ == "path", op.parameters)))

    r = path_parameters - allowed_path_parameters
    if r:
        raise SpecError(f"Parameter name{'s' if len(r) > 1 else ''} not found in path: {', '.join(sorted(r))}")
