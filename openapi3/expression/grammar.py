from ._grammar import RuntimeExpressionBuffer, RuntimeExpressionParser

def loads(data, trace=False, colorize=False):
    from .model import RuntimeExpressionModelBuilderSemantics, RuntimeExpression, Expression, JSONPointer, Body, Header, Query, Path
    parser = RuntimeExpressionParser()
    model = parser.parse(data,
                         trace=trace, colorize=colorize,
                         tokenizercls=RuntimeExpressionBuffer,
                         semantics=RuntimeExpressionModelBuilderSemantics(types=[RuntimeExpression, Expression, JSONPointer, Body, Header, Query, Path]),
                         filename='…')
    return model