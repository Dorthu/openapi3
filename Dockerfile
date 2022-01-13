FROM python:3.7-slim-buster

WORKDIR /app
COPY setup.cfg pyproject.toml requirements.txt /app/
COPY aiopenapi3/ /app/aiopenapi3
COPY tests /app/tests
RUN ls -al /app
RUN pip install --upgrade pip
RUN pip install ".[compat]"
RUN pip install ".[tests]"
