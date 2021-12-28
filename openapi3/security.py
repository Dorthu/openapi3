from typing import Optional, Dict

from pydantic import Field

from .object_base import ObjectExtended


class OAuthFlow(ObjectExtended):
    """
    Configuration details for a supported OAuth Flow

    .. here: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.1.md#oauth-flow-object
    """
    authorizationUrl: Optional[str] = Field(default=None)
    tokenUrl: Optional[str] = Field(default=None)
    refreshUrl: Optional[str] = Field(default=None)
    scopes: Dict[str, str] = Field(default_factory=dict)


class OAuthFlows(ObjectExtended):
    """
    Allows configuration of the supported OAuth Flows.

    .. here: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.1.md#oauth-flows-object
    """
    implicit: Optional[OAuthFlow] = Field(default=None)
    password: Optional[OAuthFlow] = Field(default=None)
    clientCredentials: Optional[OAuthFlow] = Field(default=None)
    authorizationCode: Optional[OAuthFlow] = Field(default=None)


class SecurityScheme(ObjectExtended):
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
