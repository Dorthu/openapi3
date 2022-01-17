from typing import Optional, Dict, List

from pydantic import Field, BaseModel, root_validator

from ..base import ObjectExtended


class SecurityScheme(ObjectExtended):
    """
    Allows the definition of a security scheme that can be used by the operations.

    https://swagger.io/specification/v2/#security-scheme-object
    """

    type: str = Field(...)
    description: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None)
    in_: Optional[str] = Field(default=None, alias="in")

    flow: Optional[str] = Field(default=None)
    authorizationUrl: Optional[str] = Field(default=None)
    tokenUrl: Optional[str] = Field(default=None)
    refreshUrl: Optional[str] = Field(default=None)
    scopes: Dict[str, str] = Field(default_factory=dict)

    @root_validator
    def validate_SecurityScheme(cls, values):
        if values["type"] == "apiKey":
            assert values["name"], "name is required for apiKey"
            assert values["in_"] in frozenset(["query", "header"]), "in must be query or header"
        return values


class SecurityRequirement(BaseModel):
    """
    Lists the required security schemes to execute this operation.

    https://swagger.io/specification/v2/#security-requirement-object
    """

    __root__: Dict[str, List[str]]
