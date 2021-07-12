#!/usr/bin/env python3
from io import open
from setuptools import setup
from os import path
import subprocess


here = path.abspath(path.dirname(__file__))


# get the long description from the README.rst
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name="openapi3",
    version='1.5.0',
    description="Client and Validator of OpenAPI 3 Specifications",
    long_description=long_description,
    author="dorthu",
    url="https://github.com/dorthu/openapi3",
    packages=['openapi3'],
    license="BSD 3-Clause License",
    install_requires=["PyYaml", "requests"],
    tests_require=["pytest"],
)
