import errno
import uuid
from typing import Optional

import starlette.status
from fastapi import Query, Body, Response, APIRouter
from fastapi.responses import JSONResponse
from fastapi_versioning import version

from . import schema

from fastapi_versioning import versioned_api_route

router = APIRouter(route_class=versioned_api_route(2))

ZOO = dict()


def _idx(l):
    for i in range(l):
        yield i


idx = _idx(100)


@router.post(
    "/pet",
    operation_id="createPet",
    response_model=schema.Pet,
    responses={201: {"model": schema.Pet}, 409: {"model": schema.Error}},
)
def createPet(
    response: Response,
    pet: schema.Pet = Body(..., embed=True),
) -> None:
    # if isinstance(pet, Cat):
    #     pet = pet.__root__
    # elif isinstance(pet, Dog):
    #     pass
    if pet.name in ZOO:
        return JSONResponse(
            status_code=starlette.status.HTTP_409_CONFLICT,
            content=schema.Error(code=errno.EEXIST, message=f"{pet.name} already exists").dict(),
        )
    pet.identifier = str(uuid.uuid4())
    ZOO[pet.name] = r = pet
    response.status_code = starlette.status.HTTP_201_CREATED
    return r


@router.get("/pet", operation_id="listPet", response_model=schema.Pets)
def listPet(limit: Optional[int] = None) -> schema.Pets:
    return list(ZOO.values())


@router.get(
    "/pets/{pet_id}", operation_id="getPet", response_model=schema.Pet, responses={404: {"model": schema.Error}}
)
def getPet(pet_id: str = Query(..., alias="petId")) -> schema.Pets:
    for k, v in ZOO.items():
        if pet_id == v.identifier:
            return v
    else:
        return JSONResponse(
            status_code=starlette.status.HTTP_404_NOT_FOUND,
            content=schema.Error(code=errno.ENOENT, message=f"{pet_id} not found").dict(),
        )


@router.delete(
    "/pets/{pet_id}", operation_id="deletePet", responses={204: {"model": None}, 404: {"model": schema.Error}}
)
def deletePet(response: Response, pet_id: int = Query(..., alias="petId")) -> schema.Pets:
    for k, v in ZOO.items():
        if pet_id == v.identifier:
            del ZOO[k]
            response.status_code = starlette.status.HTTP_204_NO_CONTENT
            return response
    else:
        return JSONResponse(
            status_code=starlette.status.HTTP_404_NOT_FOUND,
            content=schema.Error(code=errno.ENOENT, message=f"{pet_id} not found").dict(),
        )
