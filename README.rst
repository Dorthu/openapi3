openapi3
========

A Python `OpenAPI 3 Specification`_ client and validator for Python 3.

.. image:: https://github.com/Dorthu/openapi3/actions/workflows/main.yml/badge.svg
   :alt: GitHub Actions Build Badge

.. image:: https://badge.fury.io/py/openapi3.svg
   :target: https://badge.fury.io/py/openapi3


Validation Mode
---------------

This module can be run against a spec file to validate it like so::

   python3 -m openapi3 /path/to/spec

Usage as a Client
-----------------

This library also functions as an interactive client for arbitrary OpenAPI 3
specs. For example, using `Linode's OpenAPI 3 Specification`_ for reference::

   from openapi3 import OpenAPI
   import yaml

   # load the spec file and read the yaml
   with open('openapi.yaml') as f:
       spec = yaml.safe_load(f.read())

   # parse the spec into python - this will raise if the spec is invalid
   api = OpenAPI(spec)

   # call operations and receive result models
   regions = api.call_getRegions()

   # authenticate using a securityScheme defined in the spec's components.securitySchemes
   api.authenticate('personalAccessToken', my_token)

   # call an operation that requires authentication
   linodes  = api.call_getLinodeInstances()

   # call an opertaion with parameters
   linode = api.call_getLinodeInstance(parameters={"linodeId": 123})

   # the models returns are all of the same (generated) type
   print(type(linode))                      # openapi.schemas.Linode
   type(linode) == type(linodes.data[0])    # True

   # call an operation with a request body
   new_linode = api.call_createLinodeInstance(data={"region":"us-east","type":"g6-standard-2"})

   # the returned models is still of the correct type
   type(new_linode) == type(linode)     # True

HTTP basic authentication and HTTP digest authentication works like this::

   # authenticate using a securityScheme defined in the spec's components.securitySchemes
   # Tuple with (username, password) as second argument
   api.authenticate('basicAuth', ('username', 'password'))

Running Tests
-------------

This project includes a test suite, run via ``pytest``.  To run the test suite,
ensure that you've installed the dependencies and then run ``pytest`` in the root
of this project.

Roadmap
-------

The following features are planned for the future:

* Request body models, creation, and validation.
* Parameters interface with validation and explicit typing.
* Support for more authentication types.
* Support for non-json request/response content.
* Full support for all objects defined in the specification.

.. _OpenAPI 3 Specification: https://openapis.org
.. _Linode's OpenAPI 3 Specification: https://developers.linode.com/api/v4

