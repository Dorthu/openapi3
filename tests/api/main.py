from __future__ import annotations

import errno
import uuid
from typing import Optional

import starlette.status
from fastapi import FastAPI, Query, Body, Response
from fastapi.responses import JSONResponse

from fastapi_versioning import VersionedFastAPI, version

import api.v1.schema as v1
import api.v2.schema as v2

app = FastAPI(version="1.0.0",
              title="Dorthu's Petstore",
              servers=[{"url": "/", "description": "Default, relative server"}])

ZOO = dict()

def _idx(l):
    for i in range(l):
        yield i

idx = _idx(100)



@app.post('/pet',
          operation_id="createPet",
          response_model=v2.Pet,
          responses={201: {"model": v2.Pet},
                     409: {"model": v2.Error}}
          )
@version(2)
def createPet(response: Response,
              pet: v2.Pet = Body(..., embed=True),
              ) -> None:
    # if isinstance(pet, Cat):
    #     pet = pet.__root__
    # elif isinstance(pet, Dog):
    #     pass
    if pet.name in ZOO:
        return JSONResponse(status_code=starlette.status.HTTP_409_CONFLICT,
                            content=v2.Error(code=errno.EEXIST,
                                          message=f"{pet.name} already exists"
                                          ).dict()
                            )
    pet.identifier = str(uuid.uuid4())
    ZOO[pet.name] = r = pet
    response.status_code = starlette.status.HTTP_201_CREATED
    return r


@app.get('/pet',
         operation_id="listPet",
         response_model=v2.Pets)
@version(2)
def listPet(limit: Optional[int] = None) -> v2.Pets:
    return list(ZOO.values())


@app.get('/pets/{pet_id}',
         operation_id="getPet",
         response_model=v2.Pet,
         responses={
             404: {"model": v2.Error}
         }
         )
@version(2)
def getPet(pet_id: str = Query(..., alias='petId')) -> v2.Pets:
    for k, v in ZOO.items():
        if pet_id == v.identifier:
            return v
    else:
        return JSONResponse(status_code=starlette.status.HTTP_404_NOT_FOUND,
                            content=v2.Error(code=errno.ENOENT, message=f"{pet_id} not found").dict())


@app.delete('/pets/{pet_id}',
            operation_id="deletePet",
            responses={
                204: {"model": None},
                404: {"model": v2.Error}
            })
@version(2)
def deletePet(response: Response,
              pet_id: int = Query(..., alias='petId')) -> v2.Pets:
    for k, v in ZOO.items():
        if pet_id == v.identifier:
            del ZOO[k]
            response.status_code = starlette.status.HTTP_204_NO_CONTENT
            return response
    else:
        return JSONResponse(status_code=starlette.status.HTTP_404_NOT_FOUND,
                            content=v2.Error(code=errno.ENOENT, message=f"{pet_id} not found").dict())

app = VersionedFastAPI(app,
                       version_format='{major}',
                       prefix_format='/v{major}')
