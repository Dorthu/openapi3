from .object_base import ObjectBase


class Tag(ObjectBase):
    """
    A `Tag Object`_ holds a reusable set of different aspects of the OAS
    spec.

    .. _Tag Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#tagObject
    """
    __slots__ = ['name', 'description', 'externalDocs']

    def _parse_data(self):
        """
        Implementation of :any:`ObjectBase._parse_data`
        """
        self.name            = self._get('name', str)
        self.description     = self._get('description', str)
        self.externalDocs    = self._get('externalDocs', str)
