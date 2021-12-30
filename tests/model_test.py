import pydantic
import pytest

from pydantic import Extra

from tests.api.v2.schema import Pet, Dog, Cat, WhiteCat, BlackCat
from openapi3.schemas import Schema

def test_Pet():
    data = Dog.schema()
    shma = Schema.parse_obj(data)
    shma._identity = "Dog"
    assert shma.get_type().schema() == data

import asyncio
import uuid

import pytest

import requests

import uvloop
from hypercorn.asyncio import serve
from hypercorn.config import Config

import openapi3

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
    data = await asyncio.to_thread(requests.get, f"http://{server.bind[0]}/{version}/openapi.json")
    data = data.json()
    data["servers"][0]["url"] = f"http://{server.bind[0]}/{version}"
    api = openapi3.OpenAPI(data)
    return api

@pytest.mark.asyncio
async def test_model(event_loop, server, client):
    orig = client.components.schemas["WhiteCat"].dict(exclude_unset=True)
    crea = client.components.schemas["WhiteCat"].get_type().schema()
    assert orig == crea

    orig = client.components.schemas["Cat"].dict(exclude_unset=True, by_alias=True)
    crea = client.components.schemas["Cat"].get_type().schema(ref_template="#/components/schemas/{model}", by_alias=True)
    if "definitions" in crea:
        del crea["definitions"]
    assert crea == orig

    orig = client.components.schemas["Pet"].dict(exclude_unset=True, by_alias=True)
    crea = client.components.schemas["Pet"].get_type().schema(ref_template="#/components/schemas/{model}", by_alias=True)
    if "definitions" in crea:
        del crea["definitions"]
    assert crea == orig


def randomPet(client, name=None):
    if name:
        return {"pet": client.components.schemas["Dog"].model({"name":name}).dict()}
    else:
        return {"pet": client.components.schemas["WhiteCat"].model({"name":str(uuid.uuid4()), "white_name":str(uuid.uuid4())}).dict()}

@pytest.mark.asyncio
async def test_createPet(event_loop, server, client):
    data = {
        "pet": client.components.schemas["WhiteCat"].model(
            {
                "name":str(uuid.uuid4()),
                "white_name":str(uuid.uuid4())
            }).dict()
    }
#    r = await asyncio.to_thread(client.call_createPet, data=data)
    r = await asyncio.to_thread(client._.createPet, data=data)
    assert type(r.__root__.__root__).schema() == client.components.schemas["WhiteCat"].get_type().schema()

    r = await asyncio.to_thread(client.call_createPet,  data=randomPet(client, name=r.__root__.__root__.name))
    assert type(r).schema() == client.components.schemas["Error"].get_type().schema()

    with pytest.raises(pydantic.ValidationError):
        args = client._.createPet.args()
        cls = args['data'].get_type()
        cls()


@pytest.mark.asyncio
async def test_listPet(event_loop, server, client):
    r = await asyncio.to_thread(client.call_createPet, data=randomPet(client, str(uuid.uuid4())))
    l = await asyncio.to_thread(client.call_listPet)
    assert len(l) > 0

@pytest.mark.asyncio
async def test_getPet(event_loop, server, client):
    pet = await asyncio.to_thread(client.call_createPet, data=randomPet(client, str(uuid.uuid4())))
    r = await asyncio.to_thread(client.call_getPet, parameters={"pet_id":pet.__root__.identifier})
    assert type(r.__root__).schema() == type(pet.__root__).schema()

    r = await asyncio.to_thread(client.call_getPet, parameters={"pet_id":"-1"})
    assert type(r).schema() == client.components.schemas["Error"].get_type().schema()

@pytest.mark.asyncio
async def test_deletePet(event_loop, server, client):
    r = await asyncio.to_thread(client.call_deletePet, parameters={"pet_id":-1})
    assert type(r).schema() == client.components.schemas["Error"].get_type().schema()

    await asyncio.to_thread(client.call_createPet, data=randomPet(client, str(uuid.uuid4())))
    zoo = await asyncio.to_thread(client.call_listPet)
    for pet in zoo:
        while hasattr(pet, '__root__'):
            pet = pet.__root__
        await asyncio.to_thread(client.call_deletePet, parameters={"pet_id":pet.identifier})

