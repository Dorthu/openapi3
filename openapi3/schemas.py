from typing import Union, List, Any, Optional
import dataclasses

from pydantic import Field

from .errors import SpecError
from .general import Reference  # need this for Model below
from .object_base import ObjectBase, Map

TYPE_LOOKUP = {
    'array': list,
    'integer': int,
    'object': dict,
    'string': str,
    'boolean': bool,
}



class Schema(ObjectBase):
    """
    The `Schema Object`_ allows the definition of input and output data types.

    .. _Schema Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#schemaObject
    """

    title: Optional[str] = Field(default=None)
    maximum: Optional[Union[int, float]] = Field(default=None)
    minimum: Optional[Union[int, float]] = Field(default=None)
    maxLength: Optional[int] = Field(default=None)
    minLength: Optional[int] = Field(default=None)
    pattern: Optional[str] = Field(default=None)
    maxItems: Optional[int] = Field(default=None)
    minItems: Optional[int] = Field(default=None)
    required: Optional[List[str]] = Field(default_factory=list)
    enum: Optional[list] = Field(default=None)
    type: Optional[str] = Field(default=None)
    allOf: Optional[List[Union["Schema", "Reference"]]] = Field(default=None)
    oneOf: Optional[list] = Field(default=None)
    anyOf: Optional[list] = Field(default=None)
    items: Optional[Union['Schema', 'Reference']] = Field(default=None)
    properties: Optional[Map[str, Union['Schema', 'Reference']]] = Field(default=None)
    additionalProperties: Optional[Union[bool, dict]] = Field(default=None)
    description: Optional[str] = Field(default=None)
    format: Optional[str] = Field(default=None)
    default: Optional[str] = Field(default=None)  # TODO - str as a default?
    nullable: Optional[bool] = Field(default=None)
    discriminator: Optional[dict] = Field(default=None)  # 'Discriminator'
    readOnly: Optional[bool] = Field(default=None)
    writeOnly: Optional[bool] = Field(default=None)
    xml: Optional[dict] = Field(default=None)  # 'XML'
    externalDocs: Optional[dict] = Field(default=None)  # 'ExternalDocs'
    deprecated: Optional[bool] = Field(default=None)
    example: Optional[Any] = Field(default=None)
    contentEncoding: Optional[str] = Field(default=None)
    contentMediaType: Optional[str] = Field(default=None)
    contentSchema: Optional[str] = Field(default=None)

    _model_type: object = Field(default=None)
    _request_model_type: object = Field(default=None)
    _resolved_allOfs: object = Field(default=None)

    def _parse_data(self):
        """
        Implementation of :any:`ObjectBase._parse_data`
        """
        super()._parse_data()
        # TODO - Implement the following properties:
        # self.multipleOf
        # self.not
        # self.uniqueItems
        # self.maxProperties
        # self.minProperties
        # self.exclusiveMinimum
        # self.exclusiveMaximum

        self._resolved_allOfs = False

        if self.type == 'array' and self.items is None:
            raise SpecError('{}: items is required when type is "array"'.format(
                self.get_path()))

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
        if self._model_type is None:  # pylint: disable=access-member-before-definition
            type_name = self.title or self._path[-1]
            self._model_type = type(type_name, (Model,), {  # pylint: disable=attribute-defined-outside-init
                '__slots__': self.properties.keys()
            })

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
            return [self.items.get_type()(i, self.items) for i in data]
        else:
            return self.get_type()(data, self)

    def get_request_type(self):
        """
        Similar to :any:`get_type`, but the resulting type does not accept readOnly
        fields
        """
        # this is defined in ObjectBase.__init__ as all slots are
        if self._request_model_type is None:  # pylint: disable=access-member-before-definition
            type_name = self.title or self._path[-1]
            self._request_model_type = type(type_name + 'Request', (Model,), {  # pylint: disable=attribute-defined-outside-init
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

    def _resolve_allOfs(self):
        """
        Handles merging properties for allOfs
        """
        if self._resolved_allOfs:
            return

        self._resolved_allOfs = True

        if self.allOf:
            for c in self.allOf:
#            for c in typing.get_args(self.allOf):
#                assert isinstance(c, typing.ForwardRef)
#                c = ObjectBase.get_object_type(c.__forward_arg__)
                if isinstance(c, Schema):
                    self._merge(c)

    def _merge(self, other):
        """
        Merges ``other`` into this schema, preferring to use the values in ``other``
        """
        for slot in map(lambda x: x.name, dataclasses.fields(self)):
            if slot.startswith("_"):
                # skip private members
                continue

            my_value = getattr(self, slot)
            other_value = getattr(other, slot)

            if other_value:
                # we got a value to merge
                if isinstance(other_value, Schema):
                    # if it's another schema, merge them
                    if my_value is not None:
                        my_value._merge(other_value)
                    else:
                        setattr(self, slot, other_value)
                elif isinstance(other_value, list):
                    # we got a list, combine them
                    if my_value is None:
                        my_value = []
                    setattr(self, slot, my_value + other_value)
                elif isinstance(other_value, dict) or isinstance(other_value, Map):
                    if my_value:
                        for k, v in my_value.items():
                            if k in other_value:
                                if isinstance(v, Schema):
                                    v._merge(other_value[k])
                                    continue
                                else:
                                    my_value[k] = other_value[k]
                        for ok, ov in other_value.items():
                            if ok not in my_value:
                                my_value[ok] = ov
                    else:
                        setattr(self, slot, other_value)
                else:
                    setattr(self, slot, other_value)


class Model:
    """
    A Model is a representation of a Schema as a request or response.  Models
    are generated from Schema objects by called :any:`Schema.model` with the
    contents of a response.
    """
    __slots__ = ['_raw_data', '_schema']

    def __init__(self, data, schema):
        """
        Creates a new Model from data.  This should never be called directly,
        but instead should be called through :any:`Schema.model` to generate a
        Model from a defined Schema.

        :param data: The data to create this Model with
        :type data: dict
        """
        self._raw_data = data
        self._schema   = schema

        for s in self.__slots__:
            # initialize all slots to None
            setattr(self, s, None)

        # collect the data into this model
        for k, v in data.items():
            prop = schema.properties[k]

            if prop.type == 'array':
                # handle arrays
                item_schema = prop.items
                setattr(self, k, [item_schema.model(c) for c in v])
            elif prop.type == 'object':
                # handle nested objects
                object_schema = prop
                setattr(self, k, object_schema.model(v))
            else:
                setattr(self, k, v)

    def __repr__(self):
        """
        A generic representation of this model
        """
        return str(dict(self))

    def __iter__(self):
        for s in self.__slots__:
            if s.startswith('_'):
                continue
            yield s, getattr(self, s)
        return


Schema.update_forward_refs()