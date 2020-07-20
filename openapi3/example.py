from .object_base import ObjectBase


class Example(ObjectBase):
    """
    A `Example Object`_ holds a reusable set of different aspects of the OAS
    spec.

    .. _Example Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#exampleObject
    """
    __slots__ = ['summary', 'description', 'value', 'externalValue']

    def _parse_data(self):
        """
        Implementation of :any:`ObjectBase._parse_data`
        """
        self.summary         = self._get('summary', str)
        self.description     = self._get('description', str)
        self.value           = self._get('value', ['Reference', dict, str]) # 'any' type
        self.externalValue   = self._get('externalValue', str)
