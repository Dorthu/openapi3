from typing import List, Optional

from pydantic import BaseModel, Field


class PetBase(BaseModel):
    name: str
    tag: Optional[str] = None


class PetCreate(PetBase):
    pass


class Pet(PetBase):
    id: int


class Pets(BaseModel):
    __root__: List[Pet] = Field(..., description='list of pet')


class Error(BaseModel):
    code: int
    message: str