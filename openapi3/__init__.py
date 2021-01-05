from .openapi import OpenAPI
# these imports appear unused, but in fact load up the subclasses ObjectBase so
# that they may be referenced throughout the schema without issue
from . import info, servers, paths, general, schemas, components, security, tag, example
from .errors import SpecError, ReferenceResolutionError

__all__ = ['OpenAPI', 'SpecError', 'ReferenceResolutionError']
