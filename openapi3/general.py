from .object_base import ObjectBase


class ExternalDocumentation(ObjectBase):
    """
    An `External Documentation Object`_ references external resources for extended
    documentation.

    .. _External Documentation Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#externalDocumentationObject
    """

    __slots__ = ["description", "url"]
    required_fields = ["url"]

    def _parse_data(self):
        self.description = self._get("description", str)
        self.url = self._get("url", str)


class Reference(ObjectBase):
    """
    A `Reference Object`_ designates a reference to another node in the specification.

    .. _Reference Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#referenceObject
    """

    # can't start a variable name with a $
    __slots__ = ["ref", "summary", "description"]
    required_fields = ["$ref"]

    def _parse_data(self):
        self.ref = self._get("$ref", str)
        self.summary = self._get("summary", str)
        self.description = self._get("description", str)

    @classmethod
    def can_parse(cls, dct):
        """
        Override ObjectBase.can_parse because we had to remove the $ from $ref
        in __slots__ (since that's not a valid python variable name)
        """
        # TODO - can a reference object have spec extensions?
        # summary and description are optional keys; their presence shouldn't
        # affect what we can and can't parse (so remove them for the purpose of
        # checking)
        cleaned_keys = [k for k in dct.keys() if not k.startswith("x-") and k not in ("summary", "description")]

        return len(cleaned_keys) == 1 and "$ref" in dct
