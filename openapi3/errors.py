class SpecError(ValueError):
    """
    This error class is used when an invalid format is found while parsing an
    object in the spec.
    """
    def __init__(self, message, path=None, element=None):
        self.element = element
        self.message = message
        self.path    = path


class ReferenceResolutionError(SpecError):
    """
    This error class is used when resolving a reference fails, usually because
    of a malformed path in the reference.
    """
