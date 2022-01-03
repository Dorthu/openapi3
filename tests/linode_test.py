import asyncio

from aiopenapi3 import OpenAPI
import pytest


@pytest.fixture(scope="session")
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def api():
    return await OpenAPI.load_async("https://www.linode.com/docs/api/openapi.yaml")


@pytest.mark.asyncio
async def test_linode_components_schemas(api):
    for name, schema in api.components.schemas.items():
        schema.get_type().construct()


@pytest.mark.asyncio
async def test_linode_return_values(api):
    for i in api._:
        call = getattr(api._, i)
        try:
            a = call.return_value()
        except KeyError:
            pass
        else:
            a.get_type().construct()
