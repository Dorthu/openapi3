from typing import Union, List, Any, Optional, Dict

from pydantic import Field, root_validator, Extra

from ..base import ObjectExtended, SchemaBase, DiscriminatorBase
from .general import Reference
from .xml import XML


class Discriminator(ObjectExtended, DiscriminatorBase):
    """

    .. here: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#discriminator-object
    """

    propertyName: str = Field(...)
    mapping: Optional[Dict[str, str]] = Field(default_factory=dict)


class Schema(ObjectExtended, SchemaBase):
    """
    The `Schema Object`_ allows the definition of input and output data types.

    .. _Schema Object: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#schema-object
    """

    title: Optional[str] = Field(default=None)
    multipleOf: Optional[int] = Field(default=None)
    maximum: Optional[float] = Field(default=None)  # FIXME Field(discriminator='type') would be better
    exclusiveMaximum: Optional[bool] = Field(default=None)
    minimum: Optional[float] = Field(default=None)
    exclusiveMinimum: Optional[bool] = Field(default=None)
    maxLength: Optional[int] = Field(default=None)
    minLength: Optional[int] = Field(default=None)
    pattern: Optional[str] = Field(default=None)
    maxItems: Optional[int] = Field(default=None)
    minItems: Optional[int] = Field(default=None)
    uniqueItems: Optional[bool] = Field(default=None)
    maxProperties: Optional[int] = Field(default=None)
    minProperties: Optional[int] = Field(default=None)
    required: Optional[List[str]] = Field(default_factory=list)
    enum: Optional[list] = Field(default=None)

    type: Optional[str] = Field(default=None)
    allOf: Optional[List[Union["Schema", Reference]]] = Field(default_factory=list)
    oneOf: Optional[List[Union["Schema", Reference]]] = Field(default_factory=list)
    anyOf: Optional[List[Union["Schema", Reference]]] = Field(default_factory=list)
    not_: Optional[Union["Schema", Reference]] = Field(default=None, alias="not")
    items: Optional[Union["Schema", Reference]] = Field(default=None)
    properties: Optional[Dict[str, Union["Schema", Reference]]] = Field(default_factory=dict)
    additionalProperties: Optional[Union[bool, "Schema", Reference]] = Field(default=None)
    description: Optional[str] = Field(default=None)
    format: Optional[str] = Field(default=None)
    default: Optional[Any] = Field(default=None)
    nullable: Optional[bool] = Field(default=None)
    discriminator: Optional[Discriminator] = Field(default=None)  # 'Discriminator'
    readOnly: Optional[bool] = Field(default=None)
    writeOnly: Optional[bool] = Field(default=None)
    xml: Optional[XML] = Field(default=None)  # 'XML'
    externalDocs: Optional[dict] = Field(default=None)  # 'ExternalDocs'
    example: Optional[Any] = Field(default=None)
    deprecated: Optional[bool] = Field(default=None)

    _model_type: object
    _request_model_type: object

    """
    The _identity attribute is set during OpenAPI.__init__ and used at get_type()
    """
    _identity: str

    class Config:
        #        keep_untouched = (lru_cache,)
        extra = Extra.forbid

    @root_validator
    def validate_Schema_number_type(cls, values: Dict[str, object]):
        conv = ["minimum", "maximum"]
        if values.get("type", None) == "integer":
            for i in conv:
                v = values.get(i, None)
                if v is not None:
                    values[i] = int(v)
        return values


Schema.update_forward_refs()
