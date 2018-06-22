openapi3-parser
===============

.. highlight:: python

A Python `OpenAPI Specification`_ parser and library.

.. image:: https://travis-ci.org/Dorthu/openapi3-parser.svg?branch=master
    :target: https://travis-ci.org/Dorthu/openapi3-parser

.. note::
   This is a work in progress, and may change significantly in the future.  Many
   features are presently absent, and many common cases may not be implemented.

Validation Mode
---------------

This module can be run against a spec file to validate it like so::

   python -m openapi /path/to/spec

Intended Usage
--------------

This library is a combination of spec parser/validator and client.  Here is an
example, using `Linode's OpenAPI 3 Specification`_ for reference::

   # load the spec file and read the yaml
   with open('openapi.yaml') as f:
       spec = yaml.load(f.read())

   # parse the spec into python - this will raise if the spec is invalid
   api = OpenAPI(spec)

   # call operations and receive result models
   regions = api.call_getRegions()

   # authenticate using a securityScheme defined in the spec's components.securtiySchemes
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

Roadmap
-------

The following still needs to be done:

* Support for more authentication types
* Support for non-json request/response content
* Full support for all objected defined in the specification.

.. _OpenAPI Specification: https://openapis.org
.. _Linode's OpenAPI 3 Specification: https://developers.linode.com/api/v4
