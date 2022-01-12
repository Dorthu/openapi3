import os
import asyncio

from aiopenapi3 import OpenAPI
import pytest


noci = pytest.mark.skipif(os.environ.get("GITHUB_ACTIONS", None) is not None, reason="fails on github")


@pytest.fixture(scope="session")
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def api():
    from aiopenapi3.loader import NullLoader, YAMLCompatibilityLoader

    return await OpenAPI.load_async(
        "https://www.linode.com/docs/api/openapi.yaml", loader=NullLoader(YAMLCompatibilityLoader)
    )


@pytest.mark.asyncio
@noci
async def test_linode_components_schemas(api):
    for name, schema in api.components.schemas.items():
        schema.get_type().construct()


@pytest.mark.asyncio
@noci
async def test_linode_return_values(api):
    for i in api._:
        call = getattr(api._, i)
        try:
            a = call.return_value()
        except KeyError:
            pass
        else:
            a.get_type().construct()
