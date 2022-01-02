_model.py: generate

_grammar.py: generate

generate:
	python3 -m tatsu grammar.ebnf --name RuntimeExpression --outfile _grammar.py --object-model-outfile _model.py

all: generate