from typing import List, TypeVar, Union, Dict, Tuple, Optional, Callable, TypeVar, Generic
from pydantic import BaseModel, validator, ValidationError
from pydantic.generics import GenericModel

T = TypeVar('T')


class GFIResponse(GenericModel, Generic[T]):
    """
    A response from the GFI API.
    result: The result of the request.
    data: The data returned by the API.
    """
    result: T
    code: int


class RepoQuery(BaseModel):
    name: str
    owner: str