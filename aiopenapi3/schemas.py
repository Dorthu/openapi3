import types
import uuid
from typing import Union, List, Any, Optional, Dict, Literal, Annotated

from pydantic import Field, root_validator, Extra, BaseModel

from .general import Reference  # need this for Model below
from .object_base import ObjectExtended
from .xml import XML

TYPE_LOOKUP = {
    "array": list,
    "integer": int,
    "object": dict,
    "string": str,
    "boolean": bool,
}


class Discriminator(ObjectExtended):
    """

    .. here: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#discriminator-object
    """

    propertyName: str = Field(...)
    mapping: Optional[Dict[str, str]] = Field(default_factory=dict)


class Schema(ObjectExtended):
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
    default: Optional[str] = Field(default=None)  # TODO - str as a default?
    nullable: Optional[bool] = Field(default=None)
    discriminator: Optional[Discriminator] = Field(default=None)  # 'Discriminator'
    readOnly: Optional[bool] = Field(default=None)
    writeOnly: Optional[bool] = Field(default=None)
    xml: Optional[XML] = Field(default=None)  # 'XML'
    externalDocs: Optional[dict] = Field(default=None)  # 'ExternalDocs'
    example: Optional[Any] = Field(default=None)
    deprecated: Optional[bool] = Field(default=None)
    #    contentEncoding: Optional[str] = Field(default=None)
    #    contentMediaType: Optional[str] = Field(default=None)
    #    contentSchema: Optional[str] = Field(default=None)

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

    #    @lru_cache
    def get_type(self, names: List[str] = None, discriminators: List[Discriminator] = None):
        return Model.from_schema(self, names, discriminators)

    def model(self, data: Dict):
        """
        Generates a model representing this schema from the given data.

        :param data: The data to create the model from.  Should match this schema.
        :type data: dict

        :returns: A new :any:`Model` created in this Schema's type from the data.
        :rtype: self.get_type()
        """
        if self.type in ("string", "number"):
            assert len(self.properties) == 0
            # more simple types
            # if this schema represents a simple type, simply return the data
            # TODO - perhaps assert that the type of data matches the type we
            # expected
            return data
        elif self.type == "array":
            return [self.items.get_type().parse_obj(i) for i in data]
        else:
            return self.get_type().parse_obj(data)


class Model(BaseModel):
    class Config:
        extra: Extra.forbid

    @classmethod
    def from_schema(cls, shma: Schema, shmanm: List[str] = None, discriminators: List[Discriminator] = None):

        if shmanm is None:
            shmanm = []

        if discriminators is None:
            discriminators = []

        def typeof(schema: Schema):
            r = None
            if schema.type == "integer":
                r = int
            elif schema.type == "number":
                r = float
            elif schema.type == "string":
                r = str
            elif schema.type == "boolean":
                r = bool
            elif schema.type == "array":
                r = List[schema.items.get_type()]
            elif schema.type == "object":
                return schema.get_type()
            elif schema.type is None:  # discriminated root
                return None
            else:
                raise TypeError(schema.type)

            return r

        def annotationsof(schema: Schema):
            annos = dict()
            if schema.type == "array":
                annos["__root__"] = typeof(schema)
            else:

                for name, f in schema.properties.items():
                    r = None
                    for discriminator in discriminators:
                        if name != discriminator.propertyName:
                            continue
                        for disc, v in discriminator.mapping.items():
                            if v in shmanm:
                                r = Literal[disc]
                                break
                        else:
                            raise ValueError(schema)
                        break
                    else:
                        r = typeof(f)
                    if name not in schema.required:
                        annos[name] = Optional[r]
                    else:
                        annos[name] = r
            return annos

        def fieldof(schema: Schema):
            r = dict()
            if schema.type == "array":
                return r
            else:
                for name, f in schema.properties.items():
                    args = dict()
                    for i in ["enum", "default"]:
                        v = getattr(f, i, None)
                        if v:
                            args[i] = v
                    r[name] = Field(**args)
            return r

        # do not create models for primitive types
        if shma.type in ("string", "integer"):
            return typeof(shma)

        type_name = shma.title or shma._identity if hasattr(shma, "_identity") else str(uuid.uuid4())
        namespace = dict()
        annos = dict()
        if shma.allOf:
            for i in shma.allOf:
                annos.update(annotationsof(i))
        elif shma.anyOf:
            t = tuple(
                [
                    i.get_type(names=shmanm + [i.ref], discriminators=discriminators + [shma.discriminator])
                    for i in shma.anyOf
                ]
            )
            if shma.discriminator and shma.discriminator.mapping:
                annos["__root__"] = Annotated[Union[t], Field(discriminator=shma.discriminator.propertyName)]
            else:
                annos["__root__"] = Union[t]
        elif shma.oneOf:
            t = tuple(
                [
                    i.get_type(names=shmanm + [i.ref], discriminators=discriminators + [shma.discriminator])
                    for i in shma.oneOf
                ]
            )
            if shma.discriminator and shma.discriminator.mapping:
                annos["__root__"] = Annotated[Union[t], Field(discriminator=shma.discriminator.propertyName)]
            else:
                annos["__root__"] = Union[t]
        else:
            annos = annotationsof(shma)
            namespace.update(fieldof(shma))

        namespace["__annotations__"] = annos

        m = types.new_class(type_name, (BaseModel,), {}, lambda ns: ns.update(namespace))
        m.update_forward_refs()
        return m


Schema.update_forward_refs()
