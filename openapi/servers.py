from .object_base import ObjectBase

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
        self.variables = self._get('variables', dict)

        if self.variables is not None:
            # parse the server variables
            parsed_variables = {}
            for k, v in self.variables.items():
                parsed_variables[k] = ServerVariable(self.path+[k], v)

            self.variables = parsed_variables


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
