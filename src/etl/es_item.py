from dataclasses import dataclass, field
from typing import Optional, Union


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
    imdb_rating: Optional[float] = None
    description: Optional[str] = None
    genres_names: list[str] = field(default_factory=list)
    genre: list[GenreItem] = field(default_factory=list)
    directors_names: list[str] = field(default_factory=list)
    actors_names: list[str] = field(default_factory=list)
    writers_names: list[str] = field(default_factory=list)
    actors: list[PersonItem] = field(default_factory=list)
    writers: list[PersonItem] = field(default_factory=list)
    directors: list[PersonItem] = field(default_factory=list)


ITEM_TYPES = Union[PersonItem, GenreItem, FilmItem]
