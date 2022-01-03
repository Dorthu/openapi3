from typing import Optional, Dict

from pydantic import Field, root_validator

from .object_base import ObjectExtended


class OAuthFlow(ObjectExtended):
    """
    Configuration details for a supported OAuth Flow

    .. here: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#oauth-flow-object
    """

    authorizationUrl: Optional[str] = Field(default=None)
    tokenUrl: Optional[str] = Field(default=None)
    refreshUrl: Optional[str] = Field(default=None)
    scopes: Dict[str, str] = Field(default_factory=dict)


class OAuthFlows(ObjectExtended):
    """
    Allows configuration of the supported OAuth Flows.

    .. here: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#oauth-flows-object
    """

    implicit: Optional[OAuthFlow] = Field(default=None)
    password: Optional[OAuthFlow] = Field(default=None)
    clientCredentials: Optional[OAuthFlow] = Field(default=None)
    authorizationCode: Optional[OAuthFlow] = Field(default=None)


class SecurityScheme(ObjectExtended):
    """
    A `Security Scheme`_ defines a security scheme that can be used by the operations.

    .. _Security Scheme: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#security-scheme-object
    """

    type: str = Field(...)
    description: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None)
    in_: Optional[str] = Field(default=None, alias="in")
    scheme_: Optional[str] = Field(default=None, alias="scheme")
    bearerFormat: Optional[str] = Field(default=None)
    flows: Optional[OAuthFlows] = Field(default=None)
    openIdConnectUrl: Optional[str] = Field(default=None)

    @root_validator
    def validate_SecurityScheme(cls, values):
        t = values.get("type", None)
        keys = set(map(lambda x: x[0], filter(lambda x: x[1] is not None, values.items())))
        keys -= frozenset(["type", "description"])
        if t == "apikey":
            assert keys == set(["in_", "name"])
        if t == "http":
            assert keys - frozenset(["scheme_", "bearerFormat"]) == set([])
        if t == "oauth2":
            assert keys == frozenset(["flows"])
        if t == "openIdConnect":
            assert keys - frozenset(["openIdConnectUrl"]) == set([])
        return values
