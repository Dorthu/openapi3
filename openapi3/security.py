from .errors import SpecError
from .object_base import ObjectBase, Map


class SecurityScheme(ObjectBase):
    """
    A `Security Scheme`_ defines a security scheme that can be used by the operations.

    .. _Security Scheme: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#securitySchemeObject
    """
    __slots__ = ['type', 'description', 'name', 'in', 'in_', 'scheme',
                 'bearerFormat', 'flows', 'openIdConnectUrl']
    required_fields = ['type']

    def _parse_data(self):
        """
        Implementation of :any:`ObjectBase._parse_data`
        """
        self.bearerFormat     = self._get('bearerFormat', [str])
        self.description      = self._get('description', [str])
        self.flows            = self._get('flows', dict)  # ['OAuthFlows']) TODO
        self.in_              = self._get('in', str)
        self.name             = self._get('name', [str])
        self.openIdConnectUrl = self._get('openIdConnectUrl', [str])
        self.scheme           = self._get('scheme', [str])
        self.type             = self._get('type', [str])
