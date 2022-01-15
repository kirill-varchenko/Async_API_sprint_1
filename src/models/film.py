from typing import Optional
from uuid import UUID

from models import BaseModel
from models.genre import Genre
from models.person import Person


class Film(BaseModel):
    uuid: UUID
    title: str
    imdb_rating: Optional[float] = None
    genres_names: Optional[list[str]] = None
    genre: Optional[list[Genre]] = None
    description: Optional[str] = None
    directors_names: Optional[list[str]] = None
    actors_names: Optional[list[str]] = None
    writers_names: Optional[list[str]] = None
    actors: Optional[list[Person]] = None
    writers: Optional[list[Person]] = None
    directors: Optional[list[Person]] = None
