from typing import List, Optional, Dict

from pydantic import Field

from ..base import ObjectExtended, RootBase

from .general import Reference, ExternalDocumentation
from .info import Info
from .paths import PathItem
from .schemas import Schema
from .security import SecurityScheme, SecurityRequirement
from .paths import Response
from .paths import Parameter
from .tag import Tag


class Root(ObjectExtended, RootBase):
    """
    This is the root document object for the API specification.

    https://swagger.io/specification/v2/#swagger-object
    """

    swagger: str = Field(...)
    info: Info = Field(...)
    host: Optional[str] = Field(default=None)
    basePath: Optional[str] = Field(default=None)
    schemes: Optional[List[str]] = Field(default_factory=list)
    consumes: Optional[List[str]] = Field(default_factory=list)
    produces: Optional[List[str]] = Field(default_factory=list)
    paths: Dict[str, PathItem] = Field(default_factory=dict)
    definitions: Optional[Dict[str, Schema]] = Field(default_factory=dict)
    parameters: Optional[Dict[str, Parameter]] = Field(default_factory=dict)
    responses: Optional[Dict[str, Response]] = Field(default_factory=dict)
    securityDefinitions: Optional[Dict[str, SecurityScheme]] = Field(default_factory=dict)
    security: Optional[List[SecurityRequirement]] = Field(default=None)
    tags: Optional[List[Tag]] = Field(default_factory=list)
    externalDocs: Optional[ExternalDocumentation] = Field(default=None)

    def _resolve_references(self, api):
        RootBase.resolve(api, self, self, PathItem, Reference)


Root.update_forward_refs()
