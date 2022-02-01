from typing import List, Optional, Dict

from pydantic import Field, validator

from .general import Reference, ExternalDocumentation
from .info import Info
from .parameter import Parameter
from .paths import Response, Paths, PathItem
from .schemas import Schema
from .security import SecurityScheme, SecurityRequirement
from .tag import Tag
from ..base import ObjectExtended, RootBase


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
    paths: Paths = Field(default=None)
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
