from pydantic import BaseModel
from uuid import UUID


class FilmList(BaseModel):
    uuid: UUID
    title: str
    imdb_rating: float

class Genre(BaseModel):
    uuid: UUID
    name: str

class PersonList(BaseModel):
    uuid: UUID
    full_name: str

class PersonDetail(BaseModel):
    uuid: UUID
    full_name: str
    role: str
    film_ids: list[UUID]

class FilmDetail(BaseModel):
    uuid: UUID
    title: str
    imdb_rating: float
    description: str
    genre: list[Genre]
    actors: list[PersonList]
    writers: list[PersonList]
    directors: list[PersonList]
