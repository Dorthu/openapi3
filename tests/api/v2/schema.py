import uuid
from typing import List, Optional, Literal, Union, Annotated

import pydantic
from pydantic import BaseModel, Field
from pydantic.fields import Undefined

class PetBase(BaseModel):
    identifier: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    tags: Optional[List[str]] #= Field(default_factory=list)


class BlackCat(PetBase):
    pet_type: Literal['cat']
    color: Literal['black']
    black_name: str


class WhiteCat(PetBase):
    pet_type: Literal['cat']
    color: Literal['white']
    white_name: str


# Can also be written with a custom root type
#
class Cat(BaseModel):
    __root__: Annotated[Union[BlackCat, WhiteCat], Field(discriminator='color')]

    def __getattr__(self, item):
        return getattr(self.__root__, item)

#Cat = Annotated[Union[BlackCat, WhiteCat], Field(default=Undefined, discriminator='color')]


class Dog(PetBase):
    pet_type: Literal['dog']
    name: str


#Pet = Annotated[Union[Cat, Dog], Field(default=Undefined, discriminator='pet_type')]

class Pet(BaseModel):
    __root__: Annotated[Union[Cat, Dog], Field(discriminator='pet_type')]
    def __getattr__(self, item):
        return getattr(self.__root__, item)


class Pets(BaseModel):
    __root__: List[Pet] = Field(..., description='list of pet')



class Error(BaseModel):
    code: int
    message: str