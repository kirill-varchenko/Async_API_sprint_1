from models import BaseModel
from uuid import UUID
from models.person import Person
from models.genre import Genre

class Film(BaseModel):
    uuid: UUID
    title: str
    imdb_rating: float = None
    genres_names: list[str] = None
    genre: list[Genre] = None
    description: str = None
    directors_names: list[str] = None
    actors_names: list[str] = None
    writers_names: list[str] = None
    actors: list[Person] = None
    writers: list[Person] = None
    directors: list[Person] = None