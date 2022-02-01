from typing import Any, List, Optional, Dict

from pydantic import Field, validator

from ..base import ObjectExtended, RootBase

from .components import Components
from .general import Reference
from .info import Info
from .paths import PathItem, Paths
from .security import SecurityRequirement
from .servers import Server
from .tag import Tag


class Root(ObjectExtended, RootBase):
    """
    This class represents the root of the OpenAPI schema document, as defined
    in `the spec`_

    .. _the spec: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#openapi-object
    """

    openapi: str = Field(...)
    info: Info = Field(...)
    servers: Optional[List[Server]] = Field(default_factory=list)
    paths: Paths = Field(required=True, default=None)
    components: Optional[Components] = Field(default_factory=Components)
    security: Optional[List[SecurityRequirement]] = Field(default=None)
    tags: Optional[List[Tag]] = Field(default=None)
    externalDocs: Optional[Dict[Any, Any]] = Field(default_factory=dict)

    def _resolve_references(self, api):
        RootBase.resolve(api, self, self, PathItem, Reference)


Root.update_forward_refs()
