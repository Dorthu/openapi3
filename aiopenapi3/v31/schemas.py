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

    .. _Schema Object: https://datatracker.ietf.org/doc/html/draft-bhutton-json-schema-validation-00#section-6
    """

    """
    6.1.  Validation Keywords for Any Instance Type
    """

    type: Optional[Union[str, List[str]]] = Field(default=None)
    enum: Optional[List[str]] = Field(default=None)
    const: Optional[str] = Field(default=None)

    """
    6.2.  Validation Keywords for Numeric Instances (number and integer)
    """
    multipleOf: Optional[int] = Field(default=None)
    maximum: Optional[float] = Field(default=None)  # FIXME Field(discriminator='type') would be better
    exclusiveMaximum: Optional[int] = Field(default=None)
    minimum: Optional[float] = Field(default=None)
    exclusiveMinimum: Optional[int] = Field(default=None)

    """
    6.3.  Validation Keywords for Strings
    """
    maxLength: Optional[int] = Field(default=None)
    minLength: Optional[int] = Field(default=None)
    pattern: Optional[str] = Field(default=None)

    """
    6.4.  Validation Keywords for Arrays
    """
    maxItems: Optional[int] = Field(default=None)
    minItems: Optional[int] = Field(default=None)
    uniqueItems: Optional[bool] = Field(default=None)
    maxContains: Optional[int] = Field(default=None)
    minContains: Optional[int] = Field(default=None)

    """
    6.5.  Validation Keywords for Objects
    """
    maxProperties: Optional[int] = Field(default=None)
    minProperties: Optional[int] = Field(default=None)
    required: Optional[List[str]] = Field(default_factory=list)
    dependentRequired: Dict[str, str] = Field(default_factory=dict)  # FIXME

    """
    7.  A Vocabulary for Semantic Content With "format"
    """
    format: Optional[str] = Field(default=None)

    """
    8.  A Vocabulary for the Contents of String-Encoded Data
    """
    contentEncoding: Optional[str] = Field(default=None)
    contentMediaType: Optional[str] = Field(default=None)
    contentSchema: Optional[str] = Field(default=None)

    """
    9.  A Vocabulary for Basic Meta-Data Annotations
    """
    title: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    default: Optional[Any] = Field(default=None)
    deprecated: Optional[bool] = Field(default=None)
    readOnly: Optional[bool] = Field(default=None)
    writeOnly: Optional[bool] = Field(default=None)
    examples: Optional[Any] = Field(default=None)

    """
    https://datatracker.ietf.org/doc/html/draft-handrews-json-schema-validation-02
    """

    """
    8.  The JSON Schema Core Vocabulary
    """
    id: Optional[str] = Field(default=None, alias="$id")
    schema_: Optional[str] = Field(default=None, alias="$schema")
    anchor: Optional[str] = Field(default=None, alias="$anchor")

    """
    8.2.4.  Schema References
    """
    ref: Optional[str] = Field(default=None, alias="$ref")
    recursiveRef: Optional[str] = Field(default=None, alias="$recursiveRef")
    recursiveAnchor: Optional[bool] = Field(default=None, alias="$recursiveAnchor")

    vocabulary: Optional[Dict[str, bool]] = Field(default=None, alias="$vocabulary")
    comment: Optional[str] = Field(default=None, alias="$comment")
    defs: Optional[Dict[str, Any]] = Field(default=None, alias="$defs")

    """
    https://datatracker.ietf.org/doc/html/draft-handrews-json-schema-02#section-9.2
    9.2.  Keywords for Applying Subschemas in Place
    """
    allOf: Optional[List["Schema"]] = Field(default_factory=list)
    oneOf: Optional[List["Schema"]] = Field(default_factory=list)
    anyOf: Optional[List["Schema"]] = Field(default_factory=list)
    not_: Optional["Schema"] = Field(default=None, alias="not")

    """
    9.2.2.  Keywords for Applying Subschemas Conditionally
    """
    if_: Optional["Schema"] = Field(default=None, alias="if")
    then_: Optional["Schema"] = Field(default=None, alias="then")
    else_: Optional["Schema"] = Field(default=None, alias="else")
    dependentSchemas: Optional[Dict[str, "Schema"]] = Field(default_factory=dict)

    """
    9.3.1.  Keywords for Applying Subschemas to Arrays
    """
    items: Optional[Union["Schema", List["Schema"]]] = Field(default=None)
    additionalItem: Optional["Schema"] = Field(default=None)
    unevaluatedItems: Optional["Schema"] = Field(default=None)
    contains: Optional["Schema"] = Field(default=None)

    """
    9.3.2.  Keywords for Applying Subschemas to Objects
    """
    properties: Optional[Dict[str, "Schema"]] = Field(default_factory=dict)
    patternProperties: Optional[Dict[str, str]] = Field(default_factory=dict)
    additionalProperties: Optional[Union[bool, "Schema"]] = Field(default=None)
    unevaluatedProperties: Optional["Schema"] = Field(default=None)
    propertyNames: Optional["Schema"] = Field(default=None)

    """
    The OpenAPI Specification's base vocabulary is comprised of the following keywords:
    """
    discriminator: Optional[Discriminator] = Field(default=None)  # 'Discriminator'
    xml: Optional[XML] = Field(default=None)  # 'XML'
    externalDocs: Optional[dict] = Field(default=None)  # 'ExternalDocs'
    example: Optional[Any] = Field(default=None)

    _model_type: object

    """
    The _identity attribute is set during OpenAPI.__init__ and used at get_type()
    """
    _identity: str

    class Config:
        extra = Extra.allow

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
