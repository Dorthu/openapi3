import datetime
import pathlib
from typing import Any, List, Optional, Dict, Union, Callable

import yaml
from pydantic import Field
import httpx
import yarl

from .components import Components
from .errors import ReferenceResolutionError, SpecError
from .general import Reference, JSONPointer, JSONReference
from .info import Info
from .object_base import ObjectExtended, ObjectBase
from .paths import PathItem, SecurityRequirement, _validate_parameters, Operation
from .servers import Server
from .schemas import Schema, Discriminator
from .tag import Tag
from .request import Request, AsyncRequest
from .loader import Loader

HTTP_METHODS = frozenset(["get", "delete", "head", "post", "put", "patch", "trace"])


class OpenAPI:
    @property
    def paths(self):
        return self._spec.paths

    @property
    def components(self):
        return self._spec.components

    @property
    def info(self):
        return self._spec.info

    @property
    def openapi(self):
        return self._spec.openapi

    @property
    def servers(self):
        return self._spec.servers

    @classmethod
    def load_sync(cls, url, session_factory: Callable[[], httpx.Client] = httpx.Client, loader=None):
        resp = session_factory().get(url)
        return cls.loads(url, resp.text, session_factory, loader)

    @classmethod
    async def load_async(cls, url, session_factory: Callable[[], httpx.AsyncClient] = httpx.AsyncClient, loader=None):
        async with session_factory() as client:
            resp = await client.get(url)
        return cls.loads(url, resp.text, session_factory, loader)

    @classmethod
    def loads(cls, url, data, session_factory: Callable[[], httpx.AsyncClient] = httpx.AsyncClient, loader=None):
        data = Loader.dict(pathlib.Path(url), data)
        return cls(url, data, session_factory, loader)

    def __init__(
        self,
        url,
        raw_document,
        session_factory: Callable[[], Union[httpx.Client, httpx.AsyncClient]] = httpx.AsyncClient,
        loader=None,
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
        self._cached: Dict[str, "OpenAPISpec"] = dict()

        self._spec = OpenAPISpec.parse_obj(raw_document)
        self._spec._resolve_references(self)

        for name, schema in self.components.schemas.items():
            schema._identity = name

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
                        if isinstance(content.schema_, Schema):
                            content.schema_._identity = f"{path}.{m}.{r}.{c}"

    @property
    def url(self):
        return self._base_url.join(yarl.URL(self._spec.servers[0].url))

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

        if security_scheme not in self._spec.components.securitySchemes:
            raise ValueError("{} does not accept security scheme {}".format(self.info.title, security_scheme))

        self._security = {security_scheme: value}

    def _load(self, i):
        data = self.loader.load(i)
        return OpenAPISpec.parse_obj(data)

    @property
    def _(self):
        return OperationIndex(self)

    def resolve_jr(self, root: "OpenAPISpec", obj, value: Reference):
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


class OpenAPISpec(ObjectExtended):
    """
    This class represents the root of the OpenAPI schema document, as defined
    in `the spec`_

    .. _the spec: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#openapi-object
    """

    openapi: str = Field(...)
    info: Info = Field(...)
    servers: Optional[List[Server]] = Field(default=None)
    paths: Dict[str, PathItem] = Field(required=True, default_factory=dict)
    components: Optional[Components] = Field(default_factory=Components)
    security: Optional[List[SecurityRequirement]] = Field(default=None)
    tags: Optional[List[Tag]] = Field(default=None)
    externalDocs: Optional[Dict[Any, Any]] = Field(default_factory=dict)

    def _resolve_references(self, api):
        """
        Resolves all reference objects below this object and notes their original
        value was a reference.
        """
        # don't circular import

        root = self

        def resolve(obj):
            if isinstance(obj, ObjectBase):
                for slot in filter(lambda x: not x.startswith("_"), obj.__fields_set__):
                    value = getattr(obj, slot)
                    if value is None:
                        continue

                    if isinstance(obj, PathItem) and slot == "ref":
                        ref = Reference.construct(ref=value)
                        ref._target = api.resolve_jr(root, obj, ref)
                        setattr(obj, slot, ref)

                    #                    if isinstance(obj, Discriminator) and slot == "mapping":
                    #                        mapping = dict()
                    #                        for k,v in value.items():
                    #                            mapping[k] = Reference.construct(ref=v)
                    #                        setattr(obj, slot, mapping)

                    value = getattr(obj, slot)
                    if isinstance(value, Reference):
                        value._target = api.resolve_jr(root, obj, value)
                    #                        setattr(obj, slot, resolved_value)
                    elif issubclass(type(value), ObjectBase):
                        # otherwise, continue resolving down the tree
                        resolve(value)
                    elif isinstance(value, dict):  # pydantic does not use Map
                        resolve(value)
                    elif isinstance(value, list):
                        # if it's a list, resolve its item's references
                        for item in value:
                            if isinstance(item, Reference):
                                item._target = api.resolve_jr(root, obj, item)
                            elif isinstance(item, (ObjectBase, dict, list)):
                                resolve(item)
                    elif isinstance(value, (str, int, float, datetime.datetime)):
                        continue
                    else:
                        raise TypeError(type(value))
            elif isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, Reference):
                        if v.ref:
                            v._target = api.resolve_jr(root, obj, v)
                    elif isinstance(v, (ObjectBase, dict, list)):
                        resolve(v)

        resolve(self)

    def resolve_jp(self, jp):
        """
        Given a $ref path, follows the document tree and returns the given attribute.

        :param jp: The path down the spec tree to follow
        :type jp: str #/foo/bar

        :returns: The node requested
        :rtype: ObjectBase
        :raises ValueError: if the given path is not valid
        """
        path = jp.split("/")[1:]
        node = self

        for part in path:
            part = JSONPointer.decode(part)
            if isinstance(node, dict):
                if part not in node:  # pylint: disable=unsupported-membership-test
                    raise ReferenceResolutionError(f"Invalid path {path} in Reference")
                node = node.get(part)
            else:
                if not hasattr(node, part):
                    raise ReferenceResolutionError(f"Invalid path {path} in Reference")
                node = getattr(node, part)

        return node


class OperationIndex:
    class Iter:
        def __init__(self, spec):
            self.operations = []
            self.r = 0
            pi: PathItem
            for path, pi in spec.paths.items():
                op: Operation
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
        self._spec = api._spec

    def __getattr__(self, item):
        pi: PathItem
        for path, pi in self._spec.paths.items():
            op: Operation
            for method in pi.__fields_set__ & HTTP_METHODS:
                op = getattr(pi, method)
                if op.operationId != item:
                    continue

                if issubclass(self._api._session_factory, httpx.Client):
                    return Request(self._api, method, path, op)
                if issubclass(self._api._session_factory, httpx.AsyncClient):
                    return AsyncRequest(self._api, method, path, op)

        raise ValueError(item)

    def __iter__(self):
        return self.Iter(self._spec)


OpenAPISpec.update_forward_refs()
