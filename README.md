# aiopenapi3

A Python [OpenAPI 3 Specification](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md) client and validator for Python 3.

<a href="https://codecov.io/gh/commonism/aiopenapi3" target="_blank">
    <img src="https://img.shields.io/codecov/c/github/commonism/aiopenapi3" alt="Coverage">
</a>


This project is based on [Dorthu/openapi3](github.com/Dorthu/openapi3/).

## Features
  * implements OpenAPI 3.0.3
  * object parsing via pydantic
  * request body model creation via [pydantic](https://github.com/samuelcolvin/pydantic)
  * blocking and nonblocking (asyncio) interface via [httpx](https://www.python-httpx.org/)


## Usage as a Client

This library also functions as an interactive client for arbitrary OpenAPI 3
specs. For example, using `Linode's OpenAPI 3 Specification`_ for reference:

*Unfortunately I do not have access to the Linode API to validate object creation*

### asyncio
```python
from aiopenapi3 import OpenAPI
url = "https://www.linode.com/docs/api/openapi.yaml"

api = await OpenAPI.load_async(url)

# call operations and receive result models
regions = await api._.getRegions()
```

### blocking io
```python
from aiopenapi3 import OpenAPI
url = "https://www.linode.com/docs/api/openapi.yaml"
my_token = "Gae6aikaegainoor"
api = OpenAPI.load_sync(url)

# call operations and receive result models
regions = api._.getRegions()


```

### objects
pydantic is used for the models.
https://pydantic-docs.helpmanual.io/usage/exporting_models/

```python
from aiopenapi3 import OpenAPI
url = "https://www.linode.com/docs/api/openapi.yaml"

api = await OpenAPI.load_sync(url)

# call operations and receive result models
regions = await api._.getRegions()

regions.__fields_set__
{'results', 'page', 'pages', 'data'}

import json
print(json.dumps((list(filter(lambda x: 'eu-west' in x.id, regions.data))[0]).dict(), indent=2))
{
  "id": "eu-west",
  "country": "uk",
  "capabilities": [
    "Linodes",
    "NodeBalancers",
    "Block Storage",
    "Kubernetes",
    "Cloud Firewall"
  ],
  "status": "ok",
  "resolvers": {
    "ipv4": "178.79.182.5,176.58.107.5,176.58.116.5,176.58.121.5,151.236.220.5,212.71.252.5,212.71.253.5,109.74.192.20,109.74.193.20,109.74.194.20",
    "ipv6": "2a01:7e00::9,2a01:7e00::3,2a01:7e00::c,2a01:7e00::5,2a01:7e00::6,2a01:7e00::8,2a01:7e00::b,2a01:7e00::4,2a01:7e00::7,2a01:7e00::2"
  }
}
```

#### discriminators
discriminators are supported as well, but the linode api can't be used to show how to use them.
look at [tests/model_test.py] test_model.

### authentication
```python
my_token = "Gae6aikaegainoor"
api.authenticate('personalAccessToken', my_token)

# call an operation that requires authentication
linodes  = api._.getLinodeInstances()
```

HTTP basic authentication and HTTP digest authentication works like this:
```python
# authenticate using a securityScheme defined in the spec's components.securitySchemes
# Tuple with (username, password) as second argument
api.authenticate('basicAuth', ('username', 'password'))
```

### parameters

```python
# call an opertaion with parameters
linode = api._.getLinodeInstance(parameters={"linodeId": 123})
```

### body
```python
body = api._.createLinodeInstance.args()["data"].model({"region":"us-east", "type":"g6-standard-2"})
print(json.dumps(body.dict(), indent=2))
{
  "image": null,
  "root_pass": null,
  "authorized_keys": null,
  "authorized_users": null,
  "stackscript_id": null,
  "stackscript_data": null,
  "booted": null,
  "backup_id": null,
  "backups_enabled": null,
  "swap_size": null,
  "type": "g6-standard-2",
  "region": "us-east",
  "label": null,
  "tags": null,
  "group": null,
  "private_ip": null,
  "interfaces": null
}

print(json.dumps(body.dict(exclude_unset=True), indent=2))
{
  "type": "g6-standard-2",
  "region": "us-east"
}


>>> 
new_linode = api._.createLinodeInstance(data=body)
```

## Validation Mode


This module can be run against a spec file to validate it like so::

```
python3 -m aiopenapi3 tests/fixtures/with-broken-links.yaml

6 validation errors for OpenAPISpec
paths -> /with-links -> get -> responses -> 200 -> links -> exampleWithBoth -> __root__
 operationId and operationRef are mutually exclusive, only one of them is allowed (type=value_error.spec; message=operationId and operationRef are mutually exclusive, only one of them is allowed; element=None)
paths -> /with-links -> get -> responses -> 200 -> links -> exampleWithBoth -> $ref
 field required (type=value_error.missing)
paths -> /with-links -> get -> responses -> 200 -> $ref
 field required (type=value_error.missing)
paths -> /with-links-two -> get -> responses -> 200 -> links -> exampleWithNeither -> __root__
 operationId and operationRef are mutually exclusive, one of them must be specified (type=value_error.spec; message=operationId and operationRef are mutually exclusive, one of them must be specified; element=None)
paths -> /with-links-two -> get -> responses -> 200 -> links -> exampleWithNeither -> $ref
 field required (type=value_error.missing)
paths -> /with-links-two -> get -> responses -> 200 -> $ref
 field required (type=value_error.missing)
```

## Running Tests

This project includes a test suite, run via ``pytest``.  To run the test suite,
ensure that you've installed the dependencies and then run ``pytest`` in the root
of this project.

```shell
PYTHONPATH=. pytest --cov=./ --cov-report=xml .
```




