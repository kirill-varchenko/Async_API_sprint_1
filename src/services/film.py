import json
from functools import lru_cache
from typing import Optional, Union
from uuid import UUID

from aioredis import Redis
from core.config import settings
from db.elastic import get_elastic
from db.redis import get_redis
from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import NotFoundError
from fastapi import Depends
from models.film import Film
from pydantic.json import pydantic_encoder


class FilmService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    # get_by_id возвращает объект фильма. Он опционален, так как фильм может отсутствовать в базе
    async def get_by_id(self, film_id: UUID) -> Optional[Film]:
        # Пытаемся получить данные из кеша, потому что оно работает быстрее
        key = await self._redis_key_from_id(film_id)
        film = await self._get_film_from_cache(key)
        if not film:
            # Если фильма нет в кеше, то ищем его в Elasticsearch
            film = await self._get_film_from_elastic(film_id)
            if not film:
                # Если он отсутствует в Elasticsearch, значит, фильма вообще нет в базе
                return None
            # Сохраняем фильм  в кеш
            await self._put_film_to_cache(key, film)

        return film

    async def search(self, query: str, list_parameters: dict) -> list[Film]:
        key = await self._redis_key_from_search(query, list_parameters)
        films_search = await self._get_film_from_cache(key, as_list=True)
        if not films_search:
            films_search = await self._get_film_search_from_elastic(
                query, list_parameters
            )
            if not films_search:
                return None
            await self._put_film_to_cache(key, films_search, as_list=True)

        return films_search

    async def list_films(self, filter_genre: UUID, list_parameters: dict) -> list[Film]:
        key = await self._redis_key_from_search(filter_genre, list_parameters)
        films_list = await self._get_film_from_cache(key, as_list=True)
        if not films_list:
            films_list = await self._get_film_list_from_elastic(
                filter_genre, list_parameters
            )
            if not films_list:
                return None
            await self._put_film_to_cache(key, films_list, as_list=True)

        return films_list

    async def _get_film_from_elastic(self, film_id: UUID) -> Optional[Film]:
        try:
            doc = await self.elastic.get("movies", film_id)
            return Film(**doc["_source"])
        except NotFoundError:
            return None

    async def _get_film_search_from_elastic(
        self, query: str, list_parameters: dict
    ) -> list[Film]:
        if query:
            body = {
                "query": {
                    "bool": {
                        "should": [
                            {"match": {"title": query}},
                            {"match": {"description": query}},
                        ]
                    }
                }
            }
        else:
            body = {"query": {"match_all": {}}}
        additional_params = {
            "from": (list_parameters["page_number"] - 1) * list_parameters["page_size"],
            "size": list_parameters["page_size"],
        }
        if list_parameters["sort"] == "imdb_rating":
            additional_params.update({"sort": [{"imdb_rating": {"order": "asc"}}]})
        elif list_parameters["sort"] == "-imdb_rating":
            additional_params.update({"sort": [{"imdb_rating": {"order": "desc"}}]})
        body.update(additional_params)

        doc = await self.elastic.search(index="movies", body=body)
        films = [Film(**hit["_source"]) for hit in doc["hits"]["hits"]]
        return films

    async def _get_film_list_from_elastic(
        self, filter_genre: UUID, list_parameters: dict
    ) -> list[Film]:
        if filter_genre:
            body = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "nested": {
                                    "path": "genre",
                                    "query": {
                                        "bool": {
                                            "should": [
                                                {"term": {"genre.uuid": filter_genre}}
                                            ]
                                        }
                                    },
                                }
                            }
                        ]
                    }
                }
            }
        else:
            body = {"query": {"match_all": {}}}
        additional_params = {
            "from": (list_parameters["page_number"] - 1) * list_parameters["page_size"],
            "size": list_parameters["page_size"],
        }
        if list_parameters["sort"] == "imdb_rating":
            additional_params.update({"sort": [{"imdb_rating": {"order": "asc"}}]})
        elif list_parameters["sort"] == "-imdb_rating":
            additional_params.update({"sort": [{"imdb_rating": {"order": "desc"}}]})
        body.update(additional_params)

        doc = await self.elastic.search(index="movies", body=body)
        films = [Film(**hit["_source"]) for hit in doc["hits"]["hits"]]
        return films

    # Три метода ниже генерируют строковый ключ для кэширования в редис:
    # - для кэширования одной сущности используется её UUID;
    # - для результатов поиска - префикс "film-search" (чтобы отделять от
    #   поисков в других случаях) и параметры запроса;
    # - для результатов листинга - префикс "film-list" и параметры листинга.
    async def _redis_key_from_id(self, film_id: UUID) -> str:
        return str(film_id)

    async def _redis_key_from_search(self, query, list_parameters) -> str:
        return f"film-search-{query}-{list_parameters['sort']}-{list_parameters['page_size']}-{list_parameters['page_number']}"

    async def _redis_key_from_list(self, filter_genre, list_parameters) -> str:
        return f"film-list-{filter_genre}-{list_parameters['sort']}-{list_parameters['page_size']}-{list_parameters['page_number']}"

    async def _put_film_to_cache(
        self, key: str, data: Union[Film, list[Film]], as_list: bool = False
    ):
        if as_list:
            jsoned = json.dumps(data, default=pydantic_encoder)
        else:
            jsoned = data.json()
        await self.redis.set(key, jsoned, expire=settings.FILM_CACHE_EXPIRE_IN_SECONDS)

    async def _get_film_from_cache(
        self, key: str, as_list: bool = False
    ) -> Union[Film, list[Film]]:
        data = await self.redis.get(key)
        if not data:
            return None

        if as_list:
            parsed = json.loads(data)
            res = [Film(**d) for d in parsed]
        else:
            res = Film.parse_raw(data)

        return res


@lru_cache()
def get_film_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(redis, elastic)
