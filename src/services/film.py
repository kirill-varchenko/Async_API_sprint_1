import json
from functools import lru_cache
from typing import Optional, Union
from uuid import UUID

from fastapi import Depends

from core.config import settings
from db.dependens import get_storage, get_cache, get_cache_creator
from db.elastic import ElasticStorage, AbstractStorage
from db.redis import RedisCreator, RedisStorage
from elasticsearch.exceptions import NotFoundError

from db.storage import AbstractCache, AbstractKeyCreator
from models.film import Film
from pydantic.json import pydantic_encoder


class FilmService:
    def __init__(self, db: AbstractStorage, cache: AbstractCache, cache_creator):
        self.db = db
        self.cache = cache
        self.cache_creator = cache_creator

    async def search(self, query: str, list_parameters: dict) -> Optional[list[Film]]:
        key = await self.cache_creator.get_key_from_search(query, list_parameters)
        films_search = await self.cache.get_data(key, Film, as_list=True)
        if films_search:
            return films_search

        films_search = await self.db.get_data_by_query("movies", query, Film, list_parameters)
        if not films_search:
            return None
        await self.cache.put_data(key=key, data=films_search, as_list=True, expire=settings.FILM_CACHE_EXPIRE_IN_SECONDS)

        return films_search

    # get_by_id возвращает объект фильма. Он опционален, так как фильм может отсутствовать в базе
    async def get_by_id(self, film_id: UUID) -> Optional[Film]:
        # Пытаемся получить данные из кеша, потому что оно работает быстрее
        key = await self.cache_creator.get_key_from_id(film_id)
        film_from_cache = await self.cache.get_data(key, Film)
        # film = GetData(RedisStorage(RedisRequest(key=key, model=Film))).data
        if film_from_cache:
            return film_from_cache

        # Если фильма нет в кеше, то ищем его в Elasticsearch
        # self.db.storage_request = ElasticRequesterId()
        film_from_db = await self.db.get_data_by_id(index="movies", id=film_id, model=Film)
        # film = GetData(ElasticStorage(ElasticRequestByIndex("movies", film_id))).data
        if not film_from_db:
            # Если он отсутствует в Elasticsearch, значит, фильма вообще нет в базе
            return None
        # Сохраняем фильм  в кеш
        await self.cache.put_data(key=key, data=film_from_db, expire=settings.FILM_CACHE_EXPIRE_IN_SECONDS)
        # StoragePut(RedisPutParams(RedisPutRequest(key=key, data=film, expire=settings.FILM_CACHE_EXPIRE_IN_SECONDS)))

        return film_from_db


    async def list_films(self, filter_genre: UUID, list_parameters: dict) -> Optional[list[Film]]:
        key = await self.cache_creator.get_key_from_search(filter_genre, list_parameters)
        films_list = await self.cache.get_data(key, Film, as_list=True)
        if films_list:
            return films_list

        films_list_from_db = await self.db.get_data_list_by_id("movies", filter_genre, Film, parameters=list_parameters)
        if not films_list_from_db:
            return None
        await self.cache.put_data(key=key, data=films_list_from_db, as_list=True, expire=settings.FILM_CACHE_EXPIRE_IN_SECONDS)

        return films_list_from_db

    # async def _get_film_from_elastic(self, film_id: UUID) -> Optional[Film]:
    #     try:
    #         doc = await self.elastic.get("movies", film_id)
    #         return Film(**doc["_source"])
    #     except NotFoundError:
    #         return None
    #
    # async def _get_film_search_from_elastic(
    #         self, query: str, list_parameters: dict
    # ) -> list[Film]:
    #     if query:
    #         body = {
    #             "query": {
    #                 "bool": {
    #                     "should": [
    #                         {"match": {"title": query}},
    #                         {"match": {"description": query}},
    #                     ]
    #                 }
    #             }
    #         }
    #     else:
    #         body = {"query": {"match_all": {}}}
    #     additional_params = {
    #         "from": (list_parameters["page_number"] - 1) * list_parameters["page_size"],
    #         "size": list_parameters["page_size"],
    #     }
    #     if list_parameters["sort"] == "imdb_rating":
    #         additional_params.update({"sort": [{"imdb_rating": {"order": "asc"}}]})
    #     elif list_parameters["sort"] == "-imdb_rating":
    #         additional_params.update({"sort": [{"imdb_rating": {"order": "desc"}}]})
    #     body.update(additional_params)
    #
    #     doc = await self.elastic.search(index="movies", body=body)
    #     films = [Film(**hit["_source"]) for hit in doc["hits"]["hits"]]
    #     return films
    #
    # async def _get_film_list_from_elastic(
    #         self, filter_genre: UUID, list_parameters: dict
    # ) -> list[Film]:
    #     if filter_genre:
    #         body = {
    #             "query": {
    #                 "bool": {
    #                     "must": [
    #                         {
    #                             "nested": {
    #                                 "path": "genre",
    #                                 "query": {
    #                                     "bool": {
    #                                         "should": [
    #                                             {"term": {"genre.uuid": filter_genre}}
    #                                         ]
    #                                     }
    #                                 },
    #                             }
    #                         }
    #                     ]
    #                 }
    #             }
    #         }
    #     else:
    #         body = {"query": {"match_all": {}}}
    #     additional_params = {
    #         "from": (list_parameters["page_number"] - 1) * list_parameters["page_size"],
    #         "size": list_parameters["page_size"],
    #     }
    #     if list_parameters["sort"] == "imdb_rating":
    #         additional_params.update({"sort": [{"imdb_rating": {"order": "asc"}}]})
    #     elif list_parameters["sort"] == "-imdb_rating":
    #         additional_params.update({"sort": [{"imdb_rating": {"order": "desc"}}]})
    #     body.update(additional_params)
    #
    #     doc = await self.elastic.search(index="movies", body=body)
    #     films = [Film(**hit["_source"]) for hit in doc["hits"]["hits"]]
    #     return films
    #
    # # Три метода ниже генерируют строковый ключ для кэширования в редис:
    # # - для кэширования одной сущности используется её UUID;
    # # - для результатов поиска - префикс "film-search" (чтобы отделять от
    # #   поисков в других случаях) и параметры запроса;
    # # - для результатов листинга - префикс "film-list" и параметры листинга.
    # async def _redis_key_from_id(self, film_id: UUID) -> str:
    #     return str(film_id)
    #
    # async def _redis_key_from_search(self, query, list_parameters) -> str:
    #     return f"film-search-{query}-{list_parameters['sort']}-{list_parameters['page_size']}-{list_parameters['page_number']}"
    #
    # async def _redis_key_from_list(self, filter_genre, list_parameters) -> str:
    #     return f"film-list-{filter_genre}-{list_parameters['sort']}-{list_parameters['page_size']}-{list_parameters['page_number']}"
    #
    # async def _put_film_to_cache(
    #         self, key: str, data: Union[Film, list[Film]], as_list: bool = False
    # ):
    #     if as_list:
    #         jsoned = json.dumps(data, default=pydantic_encoder)
    #     else:
    #         jsoned = data.json()
    #     await self.redis.set(key, jsoned, expire=settings.FILM_CACHE_EXPIRE_IN_SECONDS)
    #
    # async def _get_film_from_cache(
    #         self, key: str, as_list: bool = False
    # ) -> Union[Film, list[Film]]:
    #     data = await self.redis.get(key)
    #     if not data:
    #         return None
    #
    #     if as_list:
    #         parsed = json.loads(data)
    #         res = [Film(**d) for d in parsed]
    #     else:
    #         res = Film.parse_raw(data)
    #
    #     return res


@lru_cache()
def get_film_service(
        db: AbstractStorage = Depends(get_storage),
        cache: AbstractCache = Depends(get_cache),
        cache_creator: AbstractKeyCreator = Depends(get_cache_creator)
) -> FilmService:
    return FilmService(db, cache, cache_creator)
