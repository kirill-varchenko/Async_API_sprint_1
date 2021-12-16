from dataclasses import dataclass, field
from typing import Union


@dataclass
class PersonItem:
    uuid: str
    full_name: str


@dataclass
class GenreItem:
    uuid: str
    name: str


@dataclass
class FilmItem:
    uuid: str
    title: str
    imdb_rating: float = None
    genres_names: str = None
    genre: list[GenreItem] = field(default_factory=list)
    description: str = None
    directors_names: str = None
    actors_names: str = None
    writers_names: str = None
    actors: list[PersonItem] = field(default_factory=list)
    writers: list[PersonItem] = field(default_factory=list)
    directors: list[PersonItem] = field(default_factory=list)


ITEM_TYPES = Union[PersonItem, GenreItem, FilmItem]
