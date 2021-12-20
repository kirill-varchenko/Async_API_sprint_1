from functools import lru_cache
from typing import Optional
from uuid import UUID
import json

from aioredis import Redis
from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import NotFoundError
from fastapi import Depends

from db.elastic import get_elastic
from db.redis import get_redis
from models.person import Person
from models.film import Film
from pydantic.json import pydantic_encoder

PERSON_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class PersonService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, person_id: UUID) -> Person:
        person = await self._get_person_from_cache(person_id)
        if not person:
            person = await self._get_person_from_elastic(person_id)
            if not person:
                return None
            await self._put_person_to_cache(person)

        return person

    async def _get_person_from_elastic(self, person_id: UUID) -> Person:
        try:
            doc = await self.elastic.get('persons', person_id)
            person = Person(**doc['_source'])
        except NotFoundError:
            return None

        films = await self.get_films_by_person_id(person_id)

        if films:
            roles = set()
            film_ids = []
            for film in films:
                film_ids.append(film.uuid)
                if person_id in {person.uuid for person in film.actors}:
                    roles.add('actor')
                if person_id in {person.uuid for person in film.writers}:
                    roles.add('writer')
                if person_id in {person.uuid for person in film.directors}:
                    roles.add('director')
            if roles:
                person.role = ', '.join(roles)
            if film_ids:
                person.film_ids = film_ids

        return person

    async def get_films_by_person_id(self, person_id: UUID) -> list[Film]:
        films = await self._get_person_films_from_cache(person_id)
        if not films:
            films = await self._get_person_films_from_elastic(person_id)
            if not films:
                return None
            await self._put_person_films_to_cache(person_id, films)

        return films

    async def _get_person_films_from_elastic(self, person_id: UUID) -> list[Film]:
        person_film_body = {
            "_source": [
                "uuid",
                "title",
                "imdb_rating",
                "actors",
                "writers",
                "directors"
            ],
            "query": {
                "bool": {
                    "filter": {
                        "nested": {
                            "path": ["actors", "writers", "directors"],
                            "query": {
                                "bool": {
                                    "should": [
                                        {
                                            "term": {
                                                "actors.uuid": person_id
                                            }
                                        },
                                        {
                                            "term": {
                                                "writers.uuid": person_id
                                            }
                                        },
                                        {
                                            "term": {
                                                "directors.uuid": person_id
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        }
        doc = await self.elastic.search(index='movies', body=person_film_body)
        films = [Film(**hit['_source']) for hit in doc['hits']['hits']]
        return films

    async def _get_person_from_cache(self, person_id: UUID) -> Person:
        data = await self.redis.get(str(person_id))
        if not data:
            return None

        res = Person.parse_raw(data)
        return res

    async def _put_person_to_cache(self, person: Person):
        await self.redis.set(str(person.uuid), person.json(), expire=PERSON_CACHE_EXPIRE_IN_SECONDS)

    async def _get_person_films_from_cache(self, person_id: UUID) -> list[Film]:
        data = await self.redis.get(f"person_films_{person_id}")
        if not data:
            return None

        parsed = json.loads(data)
        res = [Film(**d) for d in parsed]
        return res

    async def _put_person_films_to_cache(self, person_id: UUID, films: list[Film]):
        jsoned = json.dumps(films, default=pydantic_encoder)
        await self.redis.set(f"person_films_{person_id}", jsoned, expire=PERSON_CACHE_EXPIRE_IN_SECONDS)


@lru_cache()
def get_person_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    return PersonService(redis, elastic)
