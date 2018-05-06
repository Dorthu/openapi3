from .object_base import ObjectBase

class Path(ObjectBase):
    """
    A Path object, as defined `here`_.  Path objects represent URL paths that
    may be accessed by appending them to a Server

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#paths-object
    """
    __slots__ = ['summary','description','get','put','post','delete','options',
                 'head', 'patch','trace','servers','parameters']

    def _parse_data(self):
        """
        Implementation of :any:`ObjectBase._parse_data`
        """
        # TODO - handle possible $ref
        self.summary = self._get("summary", str)
        self.description = self._get("description", str)
        self.get = self._get("get", 'Operation')
        self.put = self._get("put", 'Operation')
        self.post = self._get("post", 'Operation')
        self.delete = self._get("delete", 'Operation')
        self.options = self._get("options", 'Operation')
        self.head = self._get("head", 'Operation')
        self.patch = self._get("patch", 'Operation')
        self.trace = self._get("trace", 'Operation')
        raw_servers = self._get("servers", list)
        raw_parameters = self._get("parameters", list)

        self.servers = self.parse_list(raw_servers, 'Server')


class Operation(ObjectBase):
    """
    An Operation object as defined `here`_

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#operationObject
    """
    __slots__ = ['tags','summary','description','externalDocs','operationId',
                 'parameters','requedtBody','responses','callbacks','deprecated',
                 'security','servers']
    required_fields = ['responses']

    def _parse_data(self):
        """
        Implementation of :any:`ObjectBase._parse_data`
        """
        self.tags = self._get('tags', list)
        self.summary = self._get('summary', str)
        self.description = self._get('description', str)
        self.externalDocs = self._get('externalDocs', dict) #'ExternalDocumentation')
        self.operationId = self._get('operationId', str)
        self.parameters = self._get('parameters', list)# of 'Parameters' or 'Reference'
        self.requedtBody = self._get('requestBody', dict)# 'RequestBody' or 'Reference')
        self.responses = self._get('responses', dict)# 'Responses')
        self.callbacks = self._get('callbacks', dict)#, [dict, 'Reference'])
        self.deprecated = self._get('deprecated', bool)
        self.security = self._get('seucrity', list)# of 'Security'
        raw_servers = self._get('servers', list)

        self.servers = self.parse_list(raw_servers, 'Server')
