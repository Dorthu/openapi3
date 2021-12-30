import json

import requests


class Request:
    """
    This class is returned by instances of the OpenAPI class when members
    formatted like call_operationId are accessed, and a valid Operation is
    found, and allows calling the operation directly from the OpenAPI object
    with the configured values included.  This class is not intended to be used
    directly.
    """
    def __init__(self, api: "OpenAPI", method: str, path: str, operation: "Operation.request"):
        self.api = api
        self.spec = api._spec
        self.method = method
        self.path = path
        self.operation = operation
        self.session:requests.Session = self.api._session or requests.Session()
        self.req:requests.Request = None

    def __call__(self, *args, **kwargs):
        return self.request(*args, **kwargs)

    @property
    def security(self):
        return self.api._security


    def args(self, content_type="application/json"):
        op = self.operation
        parameters = op.parameters + self.spec.paths[self.path].parameters

        return {"parameters":parameters, "data":op.requestBody.content[content_type].schema_._target}

    def _handle_secschemes(self, security_requirement, value):
        ss = self.spec.components.securitySchemes[security_requirement.name]

        if ss.type == 'http' and ss.scheme_ == 'basic':
            self.req.auth = requests.auth.HTTPBasicAuth(*value)

        if ss.type == 'http' and ss.scheme_ == 'digest':
            self.req.auth = requests.auth.HTTPDigestAuth(*value)

        if ss.type == 'http' and ss.scheme_ == 'bearer':
            header = ss.bearerFormat or 'Bearer {}'
            self.req.headers['Authorization'] = header.format(value)

        if ss.type == 'mutualTLS':
            # TLS Client certificates (mutualTLS)
            self.req.cert = value

        if ss.type == 'apiKey':
            if ss.in_ == 'query':
                # apiKey in query parameter
                self.req.params[ss.name] = value

            if ss.in_ == 'header':
                # apiKey in query header data
                self.req.headers[ss.name] = value

            if ss.in_ == 'cookie':
                self.req.cookies = {ss.name: value}


    def _handle_parameters(self, parameters):
        # Parameters
        path_parameters = {}
        accepted_parameters = {}
        p = self.operation.parameters + self.spec.paths[self.path].parameters

        for _ in list(p):
            # TODO - make this work with $refs - can operations be $refs?
            accepted_parameters.update({_.name: _})

        for name, spec in accepted_parameters.items():
            if (parameters is None or name not in parameters):
                if spec.required:
                    raise ValueError(f'Required parameter {name} not provided')
                continue

            value = parameters[name]

            if spec.in_ == 'path':
                # The string method `format` is incapable of partial updates,
                # as such we need to collect all the path parameters before
                # applying them to the format string.
                path_parameters[name] = value

            if spec.in_ == 'query':
                self.req.params[name] = value

            if spec.in_ == 'header':
                self.req.headers[name] = value

            if spec.in_ == 'cookie':
                self.req.cookies[name] = value

        self.req.url = self.req.url.format(**path_parameters)

    def _handle_body(self, data):
        if 'application/json' in self.operation.requestBody.content:
            if not isinstance(data, (dict, list)):
                raise TypeError(data)
            body = json.dumps(data)
            self.req.data = body
            self.req.headers['Content-Type'] = 'application/json'
        else:
            raise NotImplementedError()

    def request(self, data=None, parameters=None):
        """
        Sends an HTTP request as described by this Path

        :param data: The request body to send.
        :type data: any, should match content/type
        :param parameters: The parameters used to create the path
        :type parameters: dict{str: str}
        """
        # Set request method (e.g. 'GET')
        self.req = requests.Request(self.method, cookies={})

        # Set self._request.url to base_url w/ path
        self.req.url = self.spec.servers[0].url + self.path

        if self.security and self.operation.security:
            for scheme, value in self.security.items():
                for r in filter(lambda x: x.name == scheme, self.operation.security):
                    self._handle_secschemes(r, value)
                    break
                else:
                    continue
                break
            else:
                raise ValueError(f"No security requirement satisfied (accepts {', '.join(self.operation.security.keys())})")

        if self.operation.requestBody:
            if self.operation.requestBody.required and data is None:
                raise ValueError('Request Body is required but none was provided.')

            self._handle_body(data)

        self._handle_parameters(parameters)

        # send the prepared request
        result = self.session.send(self.req.prepare())

        # spec enforces these are strings
        status_code = str(result.status_code)

        # find the response model in spec we received
        expected_response = None
        if status_code in self.operation.responses:
            expected_response = self.operation.responses[status_code]
        elif 'default' in self.operation.responses:
            expected_response = self.operation.responses['default']

        if expected_response is None:
            # TODO - custom exception class that has the response object in it
            raise ValueError(f"""Unexpected response {result.status_code} from {self.operation.operationId} (expected one of { ",".join(self.operation.responses.keys()) }), no default is defined""")

        # defined as "no content"
        if len(expected_response.content) == 0:
            return None

        content_type = result.headers['Content-Type']
        expected_media = expected_response.content.get(content_type, None)

        if expected_media is None and '/' in content_type:
            # accept media type ranges in the spec. the most specific matching
            # type should always be chosen, but if we do not have a match here
            # a generic range should be accepted if one if provided
            # https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#response-object

            generic_type = content_type.split('/')[0] + '/*'
            expected_media = expected_response.content.get(generic_type, None)

        if expected_media is None:
            err_msg = '''Unexpected Content-Type {} returned for operation {} \
                         (expected one of {})'''
            err_var = result.headers['Content-Type'], self.operation.operationId, ','.join(expected_response.content.keys())

            raise RuntimeError(err_msg.format(*err_var))

        if content_type.lower() == 'application/json':
            return expected_media.schema_.model(result.json())
        else:
            raise NotImplementedError()
