import asyncio
import uuid
import sys

import pytest

import uvloop
from hypercorn.asyncio import serve
from hypercorn.config import Config

import aiopenapi3

from api.main import app


@pytest.fixture(scope="session")
def config(unused_tcp_port_factory):
    c = Config()
    c.bind = [f"localhost:{unused_tcp_port_factory()}"]
    return c


@pytest.fixture(scope="session")
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def server(event_loop, config):
    uvloop.install()
    try:
        sd = asyncio.Event()
        task = event_loop.create_task(serve(app, config, shutdown_trigger=sd.wait))
        yield config
    finally:
        sd.set()
        await task


@pytest.fixture(scope="session")
async def client(event_loop, server):
    api = await asyncio.to_thread(aiopenapi3.OpenAPI.load_sync, f"http://{server.bind[0]}/v1/openapi.json")
    return api


def randomPet(name=None):
    return {"data": {"pet": {"name": str(name or uuid.uuid4()), "pet_type": "dog"}}}


@pytest.mark.asyncio
@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires asyncio.to_thread")
async def test_createPet(event_loop, server, client):
    r = await asyncio.to_thread(client._.createPet, **randomPet())
    assert type(r).schema() == client.components.schemas["Pet"].get_type().schema()

    r = await asyncio.to_thread(client._.createPet, data={"pet": {"name": r.name}})
    assert type(r).schema() == client.components.schemas["Error"].get_type().schema()


@pytest.mark.asyncio
@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires asyncio.to_thread")
async def test_listPet(event_loop, server, client):
    r = await asyncio.to_thread(client._.createPet, **randomPet(uuid.uuid4()))
    l = await asyncio.to_thread(client._.listPet)
    assert len(l) > 0


@pytest.mark.asyncio
@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires asyncio.to_thread")
async def test_getPet(event_loop, server, client):
    pet = await asyncio.to_thread(client._.createPet, **randomPet(uuid.uuid4()))
    r = await asyncio.to_thread(client._.getPet, parameters={"pet_id": pet.id})
    assert type(r).schema() == type(pet).schema()
    assert r.id == pet.id

    r = await asyncio.to_thread(client._.getPet, parameters={"pet_id": -1})
    assert type(r).schema() == client.components.schemas["Error"].get_type().schema()


@pytest.mark.asyncio
@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires asyncio.to_thread")
async def test_deletePet(event_loop, server, client):
    r = await asyncio.to_thread(client._.deletePet, parameters={"pet_id": -1})
    assert type(r).schema() == client.components.schemas["Error"].get_type().schema()

    await asyncio.to_thread(client._.createPet, **randomPet(uuid.uuid4()))
    zoo = await asyncio.to_thread(client._.listPet)
    for pet in zoo:
        await asyncio.to_thread(client._.deletePet, parameters={"pet_id": pet.id})
