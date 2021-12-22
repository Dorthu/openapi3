import dataclasses
from typing import Optional
from .object_base import ObjectBase, Map

@dataclasses.dataclass
class SecurityScheme(ObjectBase):
    """
    A `Security Scheme`_ defines a security scheme that can be used by the operations.

    .. _Security Scheme: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#securitySchemeObject
    """
#    __slots__ = ['type', 'description', 'name', 'in', 'in_', 'scheme',
#                 'bearerFormat', 'flows', 'openIdConnectUrl']
    required_fields = ['type']

    type: str = dataclasses.field(default=None)

    bearerFormat: Optional[str] = dataclasses.field(default=None)
    description: Optional[str] = dataclasses.field(default=None)
    flows: Optional[Map[str, str]] = dataclasses.field(default=None)  # TODO
    in_: Optional[str] = dataclasses.field(default=None)
    name: Optional[str] = dataclasses.field(default=None)
    openIdConnectUrl: Optional[str] = dataclasses.field(default=None)
    scheme: Optional[str] = dataclasses.field(default=None)


    def _parse_data(self):
        super()._parse_data()
        self.in_ = self._get("in", str)