openapi3-parser
===============

.. highlight:: python

A Python `OpenAPI Specification`_ parser and library.

.. note::
   This is a work in progress, and may change significantly in the future.  Many
   features are presently absent, and many common cases may not be implemented.

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

Roadmap
-------

The following still needs to be done:

* Support for parameters and other basic request features
* Support for more authentication types
* Support for non-json request/response content
* $ref following/resolution
* Validation mode that collects and reports spec errors without dying
* Full support for all objected defined in the specification.

.. _OpenAPI Specification: https://openapis.org
.. _Linode's OpenAPI 3 Specification: https://developers.linode.com/api/v4
