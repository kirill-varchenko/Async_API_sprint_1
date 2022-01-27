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
from models.genre import Genre
from pydantic.json import pydantic_encoder


class GenreService:
    def __init__(self, db: AbstractStorage, cache: AbstractCache, cache_creator):
        self.db = db
        self.cache = cache
        self.cache_creator = cache_creator

    async def get_by_id(self, genre_id: UUID) -> Optional[Genre]:
        key = await self.cache_creator.get_key_from_id(genre_id)
        genre = await self.cache.get_data(key, Genre)
        if genre:
            return genre

        genre_from_id = await self.db.get_data_by_id('genres', genre_id, Genre)
        if not genre_from_id:
            return None
        await self.cache.put_data(key=key, data=genre_from_id, expire=settings.GENRE_CACHE_EXPIRE_IN_SECONDS)

        return genre

    async def get_all(self) -> Optional[list[Genre]]:
        key = "genres_list"
        genres = await self.cache.get_data(key, Genre, as_list=True)
        if genres:
            return genres

        genres_from_db = await self.db.get_all_from_elastic('genres', Genre)
        if not genres_from_db:
            return None
        await self.cache.put_data(key=key, data=genres_from_db, expire=settings.GENRE_CACHE_EXPIRE_IN_SECONDS, as_list=True)

        return genres








    async def _get_genre_from_elastic(self, genre_id: UUID) -> Genre:
        try:
            doc = await self.elastic.get("genres", genre_id)
            res = Genre(**doc["_source"])
        except NotFoundError:
            res = None

        return res

    async def _get_all_genres_from_elastic(self) -> list[Genre]:
        body = {"size": 1000, "query": {"match_all": {}}}
        doc = await self.elastic.search(index="genres", body=body)
        res = [Genre(**hit["_source"]) for hit in doc["hits"]["hits"]]
        return res

    # Два метода ниже генерируют строковый ключ для кэширования в редис:
    # - для кэширования одной сущности используется её UUID;
    # - для результатов листинга всех жанров - "genres_list".
    async def _redis_key_from_id(self, genre_id: UUID) -> str:
        return str(genre_id)

    async def _redis_key_from_all(self) -> str:
        return "genres_list"

    async def _put_genre_to_cache(
        self, key: str, data: Union[Genre, list[Genre]], as_list: bool = False
    ):
        if as_list:
            jsoned = json.dumps(data, default=pydantic_encoder)
        else:
            jsoned = data.json()
        await self.redis.set(key, jsoned, expire=settings.GENRE_CACHE_EXPIRE_IN_SECONDS)

    async def _get_genre_from_cache(
        self, key: str, as_list: bool = False
    ) -> Union[Genre, list[Genre]]:
        data = await self.redis.get(key)
        if not data:
            return None

        if as_list:
            parsed = json.loads(data)
            res = [Genre(**d) for d in parsed]
        else:
            res = Genre.parse_raw(data)

        return res


@lru_cache()
def get_genre_service(
        db: AbstractStorage = Depends(get_storage),
        cache: AbstractCache = Depends(get_cache),
        cache_creator: AbstractKeyCreator = Depends(get_cache_creator)
) -> GenreService:
    return GenreService(db, cache, cache_creator)
