import dataclasses
from typing import Optional
from .object_base import ObjectBase

@dataclasses.dataclass
class ExternalDocumentation(ObjectBase):
    """
    An `External Documentation Object`_ references external resources for extended
    documentation.

    .. _External Documentation Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#externalDocumentationObject
    """

    url: str = dataclasses.field(default=None)

    description: Optional[str] = dataclasses.field(default=None)


@dataclasses.dataclass
class Reference(ObjectBase):
    """
    A `Reference Object`_ designates a reference to another node in the specification.

    .. _Reference Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#referenceObject
    """
    _required_fields_cache = frozenset(['$ref'])
    ref: str = dataclasses.field(default=None)

    def _parse_data(self):
        self.ref = self._get("$ref", str)

    @classmethod
    def can_parse(cls, dct):
        """
        Override ObjectBase.can_parse because we had to remove the $ from $ref
        in __slots__ (since that's not a valid python variable name)
        """
        # TODO - can a reference object have spec extensions?
        cleaned_keys = [k for k in dct.keys() if not k.startswith('x-')]

        return len(cleaned_keys) == 1 and '$ref' in dct
