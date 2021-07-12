from .object_base import ObjectBase


class Components(ObjectBase):
    """
    A `Components Object`_ holds a reusable set of different aspects of the OAS
    spec.

    .. _Components Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#componentsObject
    """
    __slots__ = ['schemas', 'responses', 'parameters', 'examples', 'headers',
                 'requestBodies', 'securitySchemes', 'links', 'callback']

    def _parse_data(self):
        """
        Implementation of :any:`ObjectBase._parse_data`
        """
        self.examples        = self._get('examples', ['Example', 'Reference'], is_map=True)
        self.parameters      = self._get('parameters', ['Parameter', 'Reference'], is_map=True)
        self.requestBodies   = self._get('requestBody', ['RequestBody', 'Reference'], is_map=True)
        self.responses       = self._get('responses', ['Response', 'Reference'], is_map=True)
        self.schemas         = self._get('schemas', ['Schema', 'Reference'], is_map=True)
        self.securitySchemes = self._get('securitySchemes', ['SecurityScheme', 'Reference'], is_map=True)
        # self.headers       = self._get('headers', ['Header', 'Reference'], is_map=True)
        self.links         = self._get('links', ['Link', 'Reference'], is_map=True)
        # self.callbacks     = self._get('callbacks', ['Callback', 'Reference'], is_map=True)
