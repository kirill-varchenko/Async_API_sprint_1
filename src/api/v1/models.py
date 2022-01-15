from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class FilmList(BaseModel):
    uuid: UUID
    title: str
    imdb_rating: Optional[float] = None

class Genre(BaseModel):
    uuid: UUID
    name: str

class PersonList(BaseModel):
    uuid: UUID
    full_name: str

class PersonDetail(BaseModel):
    uuid: UUID
    full_name: str
    role: Optional[str] = None
    film_ids: Optional[list[UUID]] = None

class FilmDetail(BaseModel):
    uuid: UUID
    title: str
    imdb_rating: Optional[float] = None
    description: str
    genre: list[Genre]
    actors: list[PersonList]
    writers: list[PersonList]
    directors: list[PersonList]
