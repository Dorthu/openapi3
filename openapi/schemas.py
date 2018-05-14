from .object_base import ObjectBase

class Schema(ObjectBase):
    """
    """
    __slots__ = ['title','multipleOf','maximum','exclusiveMaximum','minimum',
                 'exclusiveMinimum','maxLength','minLength','pattern','maxItems',
                 'minItems','uniqueItems','maxProperties','minProperties',
                 'required','enum','type','allOf','oneOf','anyOf','not','items',
                 'properties','additionalProperties','description','format',
                 'default','nullable','discriminator','readOnly','writeOnly',
                 'xml','externalDocs','example','deprecated']
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
