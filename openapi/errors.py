class SpecError(ValueError):
    """
    This error class is used when an invalid format is found while parsing an
    object in the spec.
    """

class ReferenceResolutionError(SpecError):
    """
    This error class is used when resolving a reference fails, usually because
    of a malformed path in the reference.
    """
