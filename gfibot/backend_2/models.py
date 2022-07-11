from typing import List, Tuple, TypeVar, Generic

from pydantic import BaseModel
from pydantic.generics import GenericModel

T = TypeVar('T')


class GFIResponse(BaseModel, Generic[T]):
    code: int=200
    result: T


class RepoQuery(BaseModel):
    owner: str
    name: str