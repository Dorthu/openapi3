import dataclasses
from typing import Optional, Dict

from pydantic import Field, BaseModel

from .object_base import ObjectBase

class OAuthFlowObject(ObjectBase):
    authorizationUrl: Optional[str] = Field(default=None)
    tokenUrl: Optional[str] = Field(default=None)
    refreshUrl: Optional[str] = Field(default=None)
    scopes: Dict[str, str] = Field(default_factory=dict)

class OAuthFlows(ObjectBase):
    implicit: Optional[OAuthFlowObject] = Field(default=None)
    password: Optional[OAuthFlowObject] = Field(default=None)
    clientCredentials: Optional[OAuthFlowObject] = Field(default=None)
    authorizationCode: Optional[OAuthFlowObject] = Field(default=None)

class SecurityScheme(ObjectBase):
    """
    A `Security Scheme`_ defines a security scheme that can be used by the operations.

    .. _Security Scheme: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#securitySchemeObject
    """

    type: str = Field(default=None)

    bearerFormat: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    flows: Optional[OAuthFlows] = Field(default=None)
    in_: Optional[str] = Field(default=None, alias="in")
    name: Optional[str] = Field(default=None)
    openIdConnectUrl: Optional[str] = Field(default=None)
    scheme_: Optional[str] = Field(default=None, alias="scheme")
