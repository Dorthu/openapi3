import dataclasses
from typing import List, Any, Dict
from pydantic import BaseModel

"""
the plugin interface replicates the suds way of  dealing with broken data/schema information
"""


class Plugin:
    pass


class Init(Plugin):
    @dataclasses.dataclass
    class Context:
        initialized: "OpenAPISpec"

    def initialized(self, ctx: "Init.Context") -> "Init.Context":
        return ctx


class Document(Plugin):
    @dataclasses.dataclass
    class Context:
        url: str
        document: Dict[str, Any]

    """
    loaded(text) -> parsed(dict)
    """

    def loaded(self, ctx: "Document.Context") -> "Document.Context":
        """modify the text before parsing"""
        return ctx

    def parsed(self, ctx: "Document.Context") -> "Document.Context":
        """modify the parsed dict before …"""
        return ctx


class Message(Plugin):
    @dataclasses.dataclass
    class Context:
        operationId: str
        marshalled: Dict[str, Any] = None
        sending: str = None
        received: str = None
        parsed: Dict[str, Any] = None
        unmarshalled: BaseModel = None

    """
    sending: marshalled(dict)-> sending(str)

    receiving: received -> parsed -> unmarshalled
    """

    def marshalled(self, ctx: "Message.Context") -> "Message.Context":
        """
        modify the dict before sending
        """
        return ctx

    def sending(self, ctx: "Message.Context") -> "Message.Context":
        """
        modify the text before sending
        """
        return ctx

    def received(self, ctx: "Message.Context") -> "Message.Context":
        """
        modify the received text
        """
        return ctx

    def parsed(self, ctx: "Message.Context") -> "Message.Context":
        """
        modify the parsed dict structure
        """
        return ctx

    def unmarshalled(self, ctx: "Message.Context") -> "Message.Context":
        """
        modify the object
        """
        return ctx


class Domain:
    def __init__(self, ctx, plugins: List[Plugin]):
        self.Context = ctx
        self.plugins = plugins

    def __getattr__(self, name: str) -> "Method":
        return Method(name, self)


class Method:
    def __init__(self, name: str, domain: Domain):
        self.name = name
        self.domain = domain

    def __call__(self, **kwargs):
        r = self.domain.Context(**kwargs)
        for plugin in self.domain.plugins:
            if (method := getattr(plugin, self.name, None)) is None:
                continue
            method(r)
        return r


class Plugins:
    _domains: Dict[str, Plugin] = {"init": Init, "document": Document, "message": Message}

    def __init__(self, plugins: List[Plugin]):
        for i in self._domains.keys():
            setattr(self, f"_{i}", self._get_domain(i, plugins))

    def _get_domain(self, name, plugins) -> "Domain":
        plugins = [p for p in filter(lambda x: isinstance(x, self._domains.get(name)), plugins)]
        return Domain(self._domains.get(name).Context, plugins)

    @property
    def init(self) -> Domain:
        return self._init

    @property
    def document(self) -> Domain:
        return self._document

    @property
    def message(self) -> "Domain":
        return self._message
