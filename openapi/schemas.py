from .object_base import ObjectBase

class Schema(ObjectBase):
    """
    The `Schema Object`_ allows the definition of input and output data types.

    .. _Schema Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#schemaObject
    """
    __slots__ = ['title','multipleOf','maximum','exclusiveMaximum','minimum',
                 'exclusiveMinimum','maxLength','minLength','pattern','maxItems',
                 'minItems','uniqueItems','maxProperties','minProperties',
                 'required','enum','type','allOf','oneOf','anyOf','not','items',
                 'properties','additionalProperties','description','format',
                 'default','nullable','discriminator','readOnly','writeOnly',
                 'xml','externalDocs','example','deprecated','_model_type']
    required_fields = []

    def _parse_data(self):
        """
        Implementation of :any:`ObjectBase._parse_data`
        """
        self.title = self._get('title', str)
        #self.multipleOf
        self.maximum = self._get('maximum', int)
        #self.exclusiveMaximum
        self.minimum = self._get('minimum', int)
        #self.exclusiveMinimum
        self.maxLength = self._get('maxLength',int)
        self.minLength = self._get('minLength', int)
        self.pattern = self._get('pattern', str)
        self.maxItems = self._get('maxItems', int)
        self.minItems = self._get('minItmes', int)
        #self.uniqueItems
        #self.maxProperties
        #self.minProperties
        self.required = self._get('required', list)
        self.enum = self._get('enum', list)
        self.type = self._get('type', str)
        self.allOf = self._get('allOf', list)
        self.oneOf = self._get('oneOf', list)
        self.anyOf = self._get('anyOf', list)
        #self.not
        self.items = self._get('items', ['Schema', 'Reference'])
        self.properties = self._get('properties', ['Schema','Reference'], is_map=True)
        self.additionalProperties = self._get('additionalProperties', [bool, dict])
        self.description = self._get('description', str)
        self.format = self._get('format', str)
        self.default = self._get('default', str) # any, must match self.type
        self.nullable = self._get('nullable', bool)
        self.discriminator = self._get('discriminator', dict)# 'Discriminator')
        self.readOnly = self._get('readOnly', bool)
        self.writeOnly = self._get('writeOnly', bool)
        self.xml = self._get('xml', dict)# 'XML')
        self.externalDocs = self._get('externalDocs', dict)# 'ExternalDocs')
        #self.example = self._get('example', any?)
        self.deprecated = self._get('deprecated', bool)


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
        if self._model_type is None:
            self._model_type = type(self.path[-1], (Model,), {
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
        return self.get_type()(data)


class Model:
    """
    A Model is a representation of a Schema as a request or response.  Models
    are generated from Schema objects by called :any:`Schema.model` with the
    contents of a response.
    """
    __slots__ = ['_raw_data']
    def __init__(self, data):
        """
        Creates a new Model from data.  This should never be called directly,
        but instead should be called through :any:`Schema.model` to generate a
        Model from a defined Schema.

        :param data: The data to create this Model with
        :type data: dict
        """
        self._raw_data = data

        # collect the data into this model
        for k, v in data.items():
            setattr(self, k, v)

    def __repr__(self):
        """
        A generic representation of this model
        """
        return str(self.__dict__())

    def __dict__(self):
        """
        This object as a dict
        """
        return {s: getattr(self, s) for s in self.__slots__ if not s.startswith('_')}
