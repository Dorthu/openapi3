import dataclasses
from typing import Optional

from pydantic import Field

from .object_base import ObjectBase, Map


class SecurityScheme(ObjectBase):
    """
    A `Security Scheme`_ defines a security scheme that can be used by the operations.

    .. _Security Scheme: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#securitySchemeObject
    """

    type: str = Field(default=None)

    bearerFormat: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    flows: Optional[Map[str, str]] = Field(default=None)  # TODO
    in_: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None)
    openIdConnectUrl: Optional[str] = Field(default=None)
    scheme: Optional[str] = Field(default=None)

    def _parse_data(self):
        super()._parse_data()
        self.in_ = self._get("in", str)