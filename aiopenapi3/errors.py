import dataclasses


class SpecError(ValueError):
    """
    This error class is used when an invalid format is found while parsing an
    object in the spec.
    """

    def __init__(self, message, element=None):
        self.message = message
        self.element = element


class ReferenceResolutionError(SpecError):
    """
    This error class is used when resolving a reference fails, usually because
    of a malformed path in the reference.
    """


class HTTPError(ValueError):
    pass


@dataclasses.dataclass
class ContentTypeError(HTTPError):
    """The content-type is unexpected"""

    content_type: str
    message: str
    response: object


@dataclasses.dataclass
class HTTPStatusError(HTTPError):
    """The HTTP Status is unexpected"""

    http_status: int
    message: str
    response: object
