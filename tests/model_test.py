import pydantic
import pytest

from pydantic import Extra

from tests.api.v2.schema import Pet, Dog, Cat, WhiteCat, BlackCat

import asyncio
import uuid

import pytest

import httpx

import uvloop
from hypercorn.asyncio import serve
from hypercorn.config import Config

import aiopenapi3
from aiopenapi3.schemas import Schema

from tests.api.main import app


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


@pytest.fixture(scope="session", params=[2])
def version(request):
    return f"v{request.param}"


@pytest.fixture(scope="session")
async def client(event_loop, server, version):
    url = f"http://{server.bind[0]}/{version}/openapi.json"
    api = await aiopenapi3.OpenAPI.load_async(url)
    return api


def test_Pet():
    data = Dog.schema()
    shma = Schema.parse_obj(data)
    shma._identity = "Dog"
    assert shma.get_type().schema() == data


@pytest.mark.asyncio
async def test_sync(event_loop, server, version):
    url = f"http://{server.bind[0]}/{version}/openapi.json"
    api = await asyncio.to_thread(aiopenapi3.OpenAPI.load_sync, url)
    return api


@pytest.mark.asyncio
async def test_model(event_loop, server, client):
    orig = client.components.schemas["WhiteCat"].dict(exclude_unset=True)
    crea = client.components.schemas["WhiteCat"].get_type().schema()
    assert orig == crea

    orig = client.components.schemas["Cat"].dict(exclude_unset=True, by_alias=True)
    crea = (
        client.components.schemas["Cat"].get_type().schema(ref_template="#/components/schemas/{model}", by_alias=True)
    )
    if "definitions" in crea:
        del crea["definitions"]
    assert crea == orig

    orig = client.components.schemas["Pet"].dict(exclude_unset=True, by_alias=True)
    crea = (
        client.components.schemas["Pet"].get_type().schema(ref_template="#/components/schemas/{model}", by_alias=True)
    )
    if "definitions" in crea:
        del crea["definitions"]
    assert crea == orig


def randomPet(client, name=None):
    if name:
        return {"pet": client.components.schemas["Dog"].model({"name": name}).dict()}
    else:
        return {
            "pet": client.components.schemas["WhiteCat"]
            .model({"name": str(uuid.uuid4()), "white_name": str(uuid.uuid4())})
            .dict()
        }


@pytest.mark.asyncio
async def test_createPet(event_loop, server, client):
    data = {
        "pet": client.components.schemas["WhiteCat"]
        .model({"name": str(uuid.uuid4()), "white_name": str(uuid.uuid4())})
        .dict()
    }
    #    r = await client._.createPet( data=data)
    r = await client._.createPet(data=data)
    assert type(r.__root__.__root__).schema() == client.components.schemas["WhiteCat"].get_type().schema()

    r = await client._.createPet(data=randomPet(client, name=r.__root__.__root__.name))
    assert type(r).schema() == client.components.schemas["Error"].get_type().schema()

    with pytest.raises(pydantic.ValidationError):
        args = client._.createPet.args()
        cls = args["data"].get_type()
        cls()


@pytest.mark.asyncio
async def test_listPet(event_loop, server, client):
    r = await client._.createPet(data=randomPet(client, str(uuid.uuid4())))
    l = await client._.listPet()
    assert len(l) > 0


@pytest.mark.asyncio
async def test_getPet(event_loop, server, client):
    pet = await client._.createPet(data=randomPet(client, str(uuid.uuid4())))
    r = await client._.getPet(parameters={"pet_id": pet.__root__.identifier})
    assert type(r.__root__).schema() == type(pet.__root__).schema()

    r = await client._.getPet(parameters={"pet_id": "-1"})
    assert type(r).schema() == client.components.schemas["Error"].get_type().schema()


@pytest.mark.asyncio
async def test_deletePet(event_loop, server, client):
    r = await client._.deletePet(parameters={"pet_id": -1})
    assert type(r).schema() == client.components.schemas["Error"].get_type().schema()

    await client._.createPet(data=randomPet(client, str(uuid.uuid4())))
    zoo = await client._.listPet()
    for pet in zoo:
        while hasattr(pet, "__root__"):
            pet = pet.__root__
        await client._.deletePet(parameters={"pet_id": pet.identifier})
