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
