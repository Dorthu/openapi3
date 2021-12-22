import dataclasses
from typing import Union

from .object_base import ObjectBase, Map

@dataclasses.dataclass(init=False)
class Components(ObjectBase):
    """
    A `Components Object`_ holds a reusable set of different aspects of the OAS
    spec.

    .. _Components Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#componentsObject
    """
    __slots__ = ['schemas', 'responses', 'parameters', 'examples', 'headers',
                 'requestBodies', 'securitySchemes', 'links', 'callback']

    examples: Map[str, Union['Example', 'Reference']]
    parameters: Map[str, Union['Parameter', 'Reference']]
    requestBodies: Map[str, Union['RequestBody', 'Reference']]
    responses: Map[str, Union['Response', 'Reference']]
    schemas: Map[str, Union['Schema', 'Reference']]
    securitySchemes: Map[str, Union['SecurityScheme', 'Reference']]
    # headers: ['Header', 'Reference'], is_map=True
    links: Map[str, Union['Link', 'Reference']]
    # callbacks: ['Callback', 'Reference'], is_map=True
