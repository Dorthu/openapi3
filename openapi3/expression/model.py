import json
from yarl import URL
import requests

import openapi3.general

from ._model import RuntimeExpressionModelBuilderSemantics as RuntimeExpressionModelBuilderSemanticsBase, \
    JSONPointer as JSONPointerBase, \
    Header as HeaderBase, \
    Query as QueryBase, \
    Path as PathBase, \
    Body as BodyBase, \
    RuntimeExpression as RuntimeExpressionBase, \
    Expression as ExpressionBase


class RuntimeExpressionModelBuilderSemantics(RuntimeExpressionModelBuilderSemanticsBase):

    def reference_token(self, ast, name=None):
        return "".join(ast)

    def escaped(self, ast):
        return "".join(ast)

#    def token(self, ast, name=None):
#        return "".join(ast)


class RuntimeExpression(RuntimeExpressionBase):
    def __init__(self, ctx=None, ast=None, parseinfo=None, **kwargs):
        super().__init__(ctx, None, parseinfo, **kwargs)
        self.expression = ast

    def eval(self, req, resp):
        return self.expression.eval(req, resp)


class Expression(ExpressionBase):
    def __init__(self, ctx=None, ast=None, parseinfo=None, **kwargs):
        super().__init__(ctx, None, parseinfo, **kwargs)
        self.root = ast.root
        self.next = ast.next

    def eval(self, req, resp):
        data = None
        item = self.root
        if item[-1] == ".":
            if item == "$request.":
                data = req
            if item == "$response.":
                data = resp

            return self.next.eval(data)
        else:
            if item == "$url":
                return req.url
            elif item == "$method":
                return req.method
            elif item == "$statusCode":
                return resp.status_code



class JSONPointer(JSONPointerBase):
    def __init__(self, ctx=None, ast=None, parseinfo=None, **kwargs):
        super().__init__(ctx, None, parseinfo, **kwargs)
        self._tokens = ast.tokens
    @property
    def tokens(self):
        for i in self._tokens:
            yield openapi3.general.JSONPointer.decode(i)


class Header(HeaderBase):
    def __init__(self, ctx=None, ast=None, parseinfo=None, **kwargs):
        super().__init__(ctx, None, parseinfo, **kwargs)
        self.key = ast.key

    def eval(self, data):
        headers = None
        if isinstance(data, requests.PreparedRequest):
            headers = data.headers
        elif isinstance(data, requests.Response):
            headers = data.headers
        if headers is None:
            return None
        return headers.get(self.key, None)


class Query(QueryBase):
    def __init__(self, ctx=None, ast=None, parseinfo=None, **kwargs):
        super().__init__(ctx, None, parseinfo, **kwargs)
        self.key = ast.key

    def eval(self, data):
        if isinstance(data, requests.PreparedRequest):
            url = URL(data.url)
        elif isinstance(data, requests.Response):
            url = None
        return url.query.get(self.key, None)


class Path(PathBase):
    def __init__(self, ctx=None, ast=None, parseinfo=None, **kwargs):
        super().__init__(ctx, None, parseinfo, **kwargs)
        self.key = ast.key

    def eval(self, data):
        return data.path.get(self.key, None)


class Body(BodyBase):
    def __init__(self, ctx=None, ast=None, parseinfo=None, **kwargs):
        super().__init__(ctx, None, parseinfo, **kwargs)
        self.fragment = ast.fragment

    def eval(self, data):
        try:
            if isinstance(data, requests.PreparedRequest):
                body = json.loads(data.body)
            elif isinstance(data, requests.Response):
                body = data.json()
        except Exception:
            return None

        data = body
        try:
            for i in self.fragment.tokens:
                if isinstance(data, list):
                    i = int(i)-1
                data = data[i]
            return data
        except KeyError:
            return None
