import dataclasses
from typing import Union, Optional

from .object_base import ObjectBase, Map

@dataclasses.dataclass
class Components(ObjectBase):
    """
    A `Components Object`_ holds a reusable set of different aspects of the OAS
    spec.

    .. _Components Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#componentsObject
    """
#    __slots__ = ['schemas', 'responses', 'parameters', 'examples', 'headers',
#                 'requestBodies', 'securitySchemes', 'links', 'callback']

    examples: Optional[Map[str, Union['Example', 'Reference']]] = dataclasses.field(default=None)
    parameters: Optional[Map[str, Union['Parameter', 'Reference']]] = dataclasses.field(default=None)
    requestBodies: Optional[Map[str, Union['RequestBody', 'Reference']]] = dataclasses.field(default=None)
    responses: Optional[Map[str, Union['Response', 'Reference']]] = dataclasses.field(default=None)
    schemas: Optional[Map[str, Union['Schema', 'Reference']]] = dataclasses.field(default=None)
    securitySchemes: Optional[Map[str, Union['SecurityScheme', 'Reference']]] = dataclasses.field(default=None)
    # headers: ['Header', 'Reference'], is_map=True
    links: Optional[Map[str, Union['Link', 'Reference']]] = dataclasses.field(default=None)
    # callbacks: ['Callback', 'Reference'], is_map=True
