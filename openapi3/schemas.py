import types
from typing import Union, List, Any, Optional, Dict


from pydantic import Field, root_validator, Extra, BaseModel

from .general import Reference  # need this for Model below
from .object_base import ObjectExtended

TYPE_LOOKUP = {
    'array': list,
    'integer': int,
    'object': dict,
    'string': str,
    'boolean': bool,
}


class Discriminator(ObjectExtended):
    """

    .. here: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.1.md#discriminator-object
    """
    propertyName: str = Field(required=True)
    mapping: Optional[Dict[str, str]] = Field(default_factory=dict)


class Schema(ObjectExtended):
    """
    The `Schema Object`_ allows the definition of input and output data types.

    .. _Schema Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#schemaObject
    """

    title: Optional[str] = Field(default=None)
    multipleOf: Optional[int] = Field(default=None)
    maximum: Optional[float] = Field(default=None) # FIXME Field(discriminator='type') would be better
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
    oneOf: Optional[list] = Field(default=None)
    anyOf: Optional[List[Union["Schema", Reference]]] = Field(default=None)
    not_: Optional[Union["Schema", Reference]] = Field(default=None, alias="not")
    items: Optional[Union['Schema', Reference]] = Field(default=None)
    properties: Optional[Dict[str, Union['Schema', Reference]]] = Field(default_factory=dict)
    additionalProperties: Optional[Union[bool, 'Schema', Reference]] = Field(default=None)
    description: Optional[str] = Field(default=None)
    format: Optional[str] = Field(default=None)
    default: Optional[str] = Field(default=None)  # TODO - str as a default?
    nullable: Optional[bool] = Field(default=None)
    discriminator: Optional[Discriminator] = Field(default=None)  # 'Discriminator'
    readOnly: Optional[bool] = Field(default=None)
    writeOnly: Optional[bool] = Field(default=None)
    xml: Optional[dict] = Field(default=None)  # 'XML'
    externalDocs: Optional[dict] = Field(default=None)  # 'ExternalDocs'
    deprecated: Optional[bool] = Field(default=None)
    example: Optional[Any] = Field(default=None)
    contentEncoding: Optional[str] = Field(default=None)
    contentMediaType: Optional[str] = Field(default=None)
    contentSchema: Optional[str] = Field(default=None)

    _model_type: object
    _request_model_type: object
    _resolved_allOfs: object
    _path: str

    class Config:
        extra = Extra.forbid

    @root_validator
    def validate_Schema_number_type(cls, values):
        conv = ["minimum","maximum"]
        if values.get("type", None) == "integer":
            for i in conv:
                v = values.get(i, None)
                if v is not None:
                    values[i] = int(v)
        return values

    def get_type(self):
        """
        Returns the Type that this schema represents.  This Type is created once
        per Schema and cached so that all instances of the same schema are the
        same Type.  For example::

           object1 = example_schema.model({"some":"json"})
           object2 = example_schema.model({"other":"json"})

           isinstance(object1, example._schema.get_type()) # true
           type(object1) == type(object2) # true
        """
        # this is defined in ObjectBase.__init__ as all slots are

        try:
            return self._model_type
        except AttributeError:

            def typeof(schema):
                r = None
                if schema.type == "string":
                    r = str
                elif schema.type == "integer":
                    r = int
                elif schema.type == "array":
                    r = schema.items.get_type()
                else:
                    raise TypeError(schema.type)

                return r
            def annotationsof(schema):
                annos = dict()
                if schema.type == "array":
                    annos["__root__"] = List[typeof(schema)]
                else:
                    for name, f in schema.properties.items():
                        r = typeof(f)
                        if name not in schema.required:
                            annos[name] = Optional[r]
                        else:
                            annos[name] = r
                return annos

            type_name = self.title or self._path
            namespace = dict()
            annos = dict()
            if self.allOf:
                for i in self.allOf:
                    annos.update(annotationsof(i))
            elif self.anyOf:
#                types = [i.get_type() for i in self.anyOf]
#                namespace["__root__"] = Union[types]
                raise NotImplementedError("anyOf")
            elif self.oneOf:
                raise NotImplementedError("oneOf")
            else:

                annos = annotationsof(self)

            namespace['__annotations__'] = annos

            self._model_type = types.new_class(type_name, (BaseModel, ), {}, lambda ns: ns.update(namespace))

        return self._model_type

    def model(self, data):
        """
        Generates a model representing this schema from the given data.

        :param data: The data to create the model from.  Should match this schema.
        :type data: dict

        :returns: A new :any:`Model` created in this Schema's type from the data.
        :rtype: self.get_type()
        """
        if self.properties is None and self.type in ('string', 'number'):  # more simple types
            # if this schema represents a simple type, simply return the data
            # TODO - perhaps assert that the type of data matches the type we
            # expected
            return data
        elif self.type == "array":
            return [self.items.get_type().parse_obj(i) for i in data]
        else:
            return self.get_type().parse_obj(data)

    def get_request_type(self):
        """
        Similar to :any:`get_type`, but the resulting type does not accept readOnly
        fields
        """
        # this is defined in ObjectBase.__init__ as all slots are
        if self._request_model_type is None:  # pylint: disable=access-member-before-definition
            type_name = self.title or self._path[-1]
            self._request_model_type = type(type_name + 'Request', (BaseModel, ),
                                            {  # pylint: disable=attribute-defined-outside-init
                '__slots__': [k for k, v in self.properties.items() if not v.readOnly]
            })

        return self._request_model_type

    def request_model(self, **kwargs):
        """
        Converts the kwargs passed into a model of writeable fields of this
        schema
        """
        # TODO - this doesn't get nested schemas
        return self.get_request_type()(kwargs, self)

Schema.update_forward_refs()