from .errors import SpecError
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

        self.servers = self.parse_list(raw_servers, 'Server', field='serers')
        self.parameters = self.parse_list(raw_parameters, ['Parameter','Reference'],
                                          field='parameters')


class Parameter(ObjectBase):
    """
    A `Parameter Object`_ defines a single operation parameter.

    .. _Parameter Object: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#parameterObject
    """
    __slots__ = ['name','in','in_','description','required','deprecated',
                 'allowEmptyValue','style','explode','allowReserved','schema',
                 'example','examples']
    required_fields = ['name','in']


    def _parse_data(self):
        self.name = self._get('name', str)
        self.in_ = self._get('in', str) # TODO must be one of ["query","header","path","cookie"]
        self.description = self._get('description', str)
        self.required = self._get('required', bool)
        self.deprecated = self._get('deprecated', bool)
        self.allowEmptyValue = self._get('allowEmptyValue', bool)

        # TODO this is an either-or with content - see docs
        self.style = self._get('style', str)
        self.explode = self._get('explode', bool)
        self.allowReserved = self._get('allowReserved', bool)
        self.schema = self._get('schema', [dict,'Reference'])#['Schema','Reference'])
        self.example = self._get('example', str)
        self.examples = self._get('examples', dict) # Map[str: ['Example','Reference']]

        # required is required and must be True if this parameter is in the path
        if self.in_ == "path" and self.required != True:
            raise SpecError("Parameter {} must be required since it is in the path".format(
                self.get_path()))

class Operation(ObjectBase):
    """
    An Operation object as defined `here`_

    .. _here: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#operationObject
    """
    __slots__ = ['tags','summary','description','externalDocs','operationId',
                 'parameters','requestBody','responses','callbacks','deprecated',
                 'security','servers']
    required_fields = ['responses']

    def _parse_data(self):
        """
        Implementation of :any:`ObjectBase._parse_data`
        """
        self.tags = self._get('tags', list)
        self.summary = self._get('summary', str)
        self.description = self._get('description', str)
        self.externalDocs = self._get('externalDocs', 'ExternalDocumentation')
        self.operationId = self._get('operationId', str)
        self.parameters = self._get('parameters', list)# of 'Parameters' or 'Reference'
        self.requestBody = self._get('requestBody', dict)# 'RequestBody' or 'Reference')
        self.responses = self._get('responses', dict)# 'Responses')
        self.callbacks = self._get('callbacks', dict)#, [dict, 'Reference'])
        self.deprecated = self._get('deprecated', bool)
        self.security = self._get('seucrity', list)# of 'Security'
        raw_servers = self._get('servers', list)

        self.servers = self.parse_list(raw_servers, 'Server')
