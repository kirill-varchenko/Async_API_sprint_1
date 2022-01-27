import json
from functools import lru_cache
from typing import Optional, Union
from uuid import UUID

from aioredis import Redis
from core.config import settings
from db.dependens import get_storage, get_cache, get_cache_creator
from db.elastic import get_elastic
from db.redis import get_redis
from elasticsearch import AsyncElasticsearch
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

    async def _get_person_from_elastic(self, person_id: UUID) -> Person:
        try:
            doc = await self.elastic.get("persons", person_id)
            person = Person(**doc["_source"])
        except NotFoundError:
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
                person.role = ", ".join(roles)
            if film_ids:
                person.film_ids = film_ids

        return person

    async def get_person_films_from_elastic(self, person_id: UUID) -> list[Film]:
        person_film_body = {
            "_source": [
                "uuid",
                "title",
                "imdb_rating",
                "actors",
                "writers",
                "directors",
            ],
            "query": {
                "bool": {
                    "should": [
                        {
                            "nested": {
                                "path": "actors",
                                "query": {
                                    "bool": {
                                        "should": [{"term": {"actors.uuid": person_id}}]
                                    }
                                },
                            }
                        },
                        {
                            "nested": {
                                "path": "writers",
                                "query": {
                                    "bool": {
                                        "should": [
                                            {"term": {"writers.uuid": person_id}}
                                        ]
                                    }
                                },
                            }
                        },
                        {
                            "nested": {
                                "path": "directors",
                                "query": {
                                    "bool": {
                                        "should": [
                                            {"term": {"directors.uuid": person_id}}
                                        ]
                                    }
                                },
                            }
                        },
                    ]
                }
            },
        }
        doc = await self.elastic.search(index="movies", body=person_film_body)
        films = [Film(**hit["_source"]) for hit in doc["hits"]["hits"]]
        return films

    async def _get_person_search_from_elastic(
        self, query: str, list_parameters: dict
    ) -> list[Person]:
        if query:
            body = {"query": {"match": {"full_name": {"query": query}}}}
        else:
            body = {"query": {"match_all": {}}}
        additional_params = {
            "from": (list_parameters["page_number"] - 1) * list_parameters["page_size"],
            "size": list_parameters["page_size"],
        }
        if list_parameters["sort"] == "full_name":
            additional_params.update({"sort": [{"full_name.raw": {"order": "asc"}}]})
        elif list_parameters["sort"] == "-full_name":
            additional_params.update({"sort": [{"full_name.raw": {"order": "desc"}}]})
        body.update(additional_params)

        doc = await self.elastic.search(index="persons", body=body)
        persons = [Person(**hit["_source"]) for hit in doc["hits"]["hits"]]
        return persons

    # Три метода ниже генерируют строковый ключ для кэширования в редис:
    # - для кэширования одной сущности используется её UUID;
    # - для результатов поиска - префикс "person-search" (чтобы отделять от
    #   поисков в других случаях) и параметры запроса;
    # - для списка фильмов по персоне - префикс "person-films" и UUID персоны.
    async def _redis_key_from_id(self, person_id: UUID) -> str:
        return str(person_id)

    async def _redis_key_from_search(self, query, list_parameters) -> str:
        return f"person-search-{query}-{list_parameters['sort']}-{list_parameters['page_size']}-{list_parameters['page_number']}"

    async def _redis_key_from_films_list(self, person_id: UUID) -> str:
        return f"person-films-{person_id}"

    async def _put_person_to_cache(
        self, key: str, data: Union[Person, list[Person]], as_list: bool = False
    ):
        if as_list:
            jsoned = json.dumps(data, default=pydantic_encoder)
        else:
            jsoned = data.json()
        await self.redis.set(key, jsoned, expire=settings.PERSON_CACHE_EXPIRE_IN_SECONDS)

    async def _get_person_from_cache(
        self, key: str, as_list: bool = False
    ) -> Union[Person, list[Person]]:
        data = await self.redis.get(key)
        if not data:
            return None

        if as_list:
            parsed = json.loads(data)
            res = [Person(**d) for d in parsed]
        else:
            res = Person.parse_raw(data)

        return res

    async def _put_person_films_to_cache(self, key: str, data: list[Film]):
        jsoned = json.dumps(data, default=pydantic_encoder)
        await self.redis.set(key, jsoned, expire=settings.PERSON_CACHE_EXPIRE_IN_SECONDS)

    async def _get_person_films_from_cache(self, key: str) -> list[Film]:
        data = await self.redis.get(key)
        if not data:
            return None

        parsed = json.loads(data)
        res = [Film(**d) for d in parsed]

        return res


@lru_cache()
def get_person_service(
        db: AbstractStorage = Depends(get_storage),
        cache: AbstractCache = Depends(get_cache),
        cache_creator: AbstractKeyCreator = Depends(get_cache_creator)
) -> PersonService:
    return PersonService(db, cache, cache_creator)
