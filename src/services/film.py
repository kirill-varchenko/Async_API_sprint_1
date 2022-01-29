from functools import lru_cache
from typing import Optional
from uuid import UUID

from fastapi import Depends

from core.config import settings
from db.dependens import get_storage, get_cache, get_cache_creator
from db.elastic import AbstractStorage

from db.storage import AbstractCache, AbstractKeyCreator
from models.film import Film


class FilmService:
    def __init__(self, db: AbstractStorage, cache: AbstractCache, cache_creator):
        self.db = db
        self.cache = cache
        self.cache_creator = cache_creator

    async def search(self, query: str, list_parameters: dict) -> Optional[list[Film]]:
        key = await self.cache_creator.get_key_from_search('film', query, list_parameters)
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
        key = await self.cache_creator.get_key_from_search('film', filter_genre, list_parameters)
        films_list = await self.cache.get_data(key, Film, as_list=True)
        if films_list:
            return films_list

        films_list_from_db = await self.db.get_data_list_by_id("movies", filter_genre, Film, parameters=list_parameters)
        if not films_list_from_db:
            return None
        await self.cache.put_data(key=key, data=films_list_from_db, as_list=True, expire=settings.FILM_CACHE_EXPIRE_IN_SECONDS)

        return films_list_from_db


@lru_cache()
def get_film_service(
        db: AbstractStorage = Depends(get_storage),
        cache: AbstractCache = Depends(get_cache),
        cache_creator: AbstractKeyCreator = Depends(get_cache_creator)
) -> FilmService:
    return FilmService(db, cache, cache_creator)
