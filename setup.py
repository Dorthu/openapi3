#!/usr/bin/env python3
from io import open
from setuptools import setup
from os import path


here = path.abspath(path.dirname(__file__))


# get the long description from the README.rst
with open(path.join(here, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()


setup(
    name="openapi3",
    version="1.6.6",
    description="Client and Validator of OpenAPI 3 Specifications",
    long_description=long_description,
    author="dorthu",
    url="https://github.com/dorthu/openapi3",
    packages=["openapi3"],
    license="BSD 3-Clause License",
    install_requires=["PyYaml", "requests"],
    extras_require={
        "test": ["pytest", "pytest-asyncio==0.16", "uvloop==0.17.0", "hypercorn==0.14.3", "pydantic==1.10.2", "fastapi==0.76.0"],
    },
)
