import dataclasses
from .object_base import ObjectBase, Map

@dataclasses.dataclass(init=False)
class SecurityScheme(ObjectBase):
    """
    A `Security Scheme`_ defines a security scheme that can be used by the operations.

    .. _Security Scheme: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#securitySchemeObject
    """
    __slots__ = ['type', 'description', 'name', 'in', 'in_', 'scheme',
                 'bearerFormat', 'flows', 'openIdConnectUrl']
    required_fields = ['type']

    bearerFormat: str
    description: str
    flows: Map[str, str]  # TODO
    in_: str
    name: str
    openIdConnectUrl: str
    scheme: str
    type: str

    def _parse_data(self):
        super()._parse_data()
        self.in_ = self._get("in", str)
