import json
from functools import lru_cache
from typing import Optional, Union
from uuid import UUID

from core.config import settings
from db.dependens import get_storage, get_cache, get_cache_creator
from elasticsearch.exceptions import NotFoundError
from fastapi import Depends

from db.storage import AbstractStorage, AbstractCache, AbstractKeyCreator
from models.film import Film
from models.person import Person
from pydantic.json import pydantic_encoder


class PersonService:
    def __init__(self, db: AbstractStorage, cache: AbstractCache, cache_creator):
        self.db = db
        self.cache = cache
        self.cache_creator = cache_creator

    async def get_by_search(self, query: str, list_parameters: dict) -> Optional[list[Person]]:
        key = await self.cache_creator.get_key_from_search('person', query, list_parameters)
        persons_search = await self.cache.get_data(key, Person, as_list=True)
        if persons_search:
            return persons_search

        persons = await self.db.get_person_search_from_elastic('persons', query, Person, list_parameters)
        if not persons:
            return None
        persons_search = [await self.get_by_id(person.uuid) for person in persons]
        await self.cache.put_data(key=key, data=persons_search, as_list=True, expire=settings.PERSON_CACHE_EXPIRE_IN_SECONDS)

        return persons_search

    async def get_by_id(self, person_id: UUID) -> Optional[Person]:
        key = await self.cache_creator.get_key_from_id(person_id)
        person = await self.cache.get_data(key, Person)
        if person:
            return person

        person_from_db = await self.db.get_data_by_id(index="persons", id=person_id, model=Person)
        if not person_from_db:
            return None

        films = await self.get_films_by_person_id(person_id)
        if films:
            roles = set()
            film_ids = []
            for film in films:
                film_ids.append(film.uuid)
                if person_id in {person.uuid for person in film.actors}:
                    roles.add("actor")
                if person_id in {person.uuid for person in film.writers}:
                    roles.add("writer")
                if person_id in {person.uuid for person in film.directors}:
                    roles.add("director")
            if roles:
                person_from_db.role = ", ".join(roles)
            if film_ids:
                person_from_db.film_ids = film_ids

        await self.cache.put_data(key=key, data=person_from_db, expire=settings.PERSON_CACHE_EXPIRE_IN_SECONDS)

        return person_from_db

    async def get_films_by_person_id(self, person_id: UUID) -> Optional[list[Film]]:
        key = await self.cache_creator.get_key_from_films_list('person', person_id)
        films = await self.cache.get_data(key, Film, as_list=True)
        if films:
            return films

        films_from_db = await self.db.get_person_films_from_elastic('movies', person_id, Film)
        if not films_from_db:
            return None
        await self.cache.put_data(key=key, data=films_from_db, as_list=True, expire=settings.PERSON_CACHE_EXPIRE_IN_SECONDS)

        return films_from_db


@lru_cache()
def get_person_service(
        db: AbstractStorage = Depends(get_storage),
        cache: AbstractCache = Depends(get_cache),
        cache_creator: AbstractKeyCreator = Depends(get_cache_creator)
) -> PersonService:
    return PersonService(db, cache, cache_creator)
