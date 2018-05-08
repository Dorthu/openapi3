from .object_base import ObjectBase, Map

class Server(ObjectBase):
    """
    The Server object, as described `here`_

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#serverObject
    """
    __slots__ = ['url','description','variables']
    required_fields=['url']

    def _parse_data(self):
        """
        Implementation of :any:`ObjectBase._parse_data`
        """
        self.url = self._get('url', str)
        self.description = self._get('description', str)
        raw_variables = self._get('variables', dict)

        self.variables =  None
        if raw_variables is not None:
            self.variables = Map(self.path+['variables'], raw_variables,
                                 ['ServerVariable'])


class ServerVariable(ObjectBase):
    """
    A ServerVariable object as defined `here`_.

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#server-variable-object
    """
    __slots__ = ['enum','default','description']
    required_fields = ['default']

    def _parse_data(self):
        """
        Implementation of :any:`ObjectBase._parse_data`
        """
        self.enum = self._get('enum', list, list_type=str)
        self.default = self._get('default', str)
        self.description = self._get('description', str)
