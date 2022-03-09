class SpecError(ValueError):
    """
    This error class is used when an invalid format is found while parsing an
    object in the spec.
    """

    def __init__(self, message, path=None, element=None):
        self.element = element
        self.message = message
        self.path = path


class ReferenceResolutionError(SpecError):
    """
    This error class is used when resolving a reference fails, usually because
    of a malformed path in the reference.
    """


class ModelError(ValueError):
    """The data supplied to the Model mismatches the models attributes"""


class UnexpectedResponseError(RuntimeError):
    """
    This error is raised if a call to an Operation results in an undocumented
    Response Code, and encapsulates the response received as well as the unexpected
    status code.
    """
    def __init__(self, response, operation):
        """
        :param response: The response object returned from the request, in full
        :type response: requests.Response
        :param operation: The operation object that was making the request
        :type operation: openapi3.Operation
        """
        # set up error message
        super().__init__(
            "Unexpected response {} from {} (expected one of {}, no default is defined)".format(
                response.status_code,
                operation.operationId,
                ", ".join(operation.responses.keys()),
            ),
        )

        #: The full response object returned from the request, of type requests.Response
        self.response = response
        #: The Operation object that made the request
        self.operation = operation
        #: A convenience field that captures the unexpected status code that
        #: triggered this exception.
        self.status_code = response.status_code
