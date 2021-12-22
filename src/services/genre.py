import json
from functools import lru_cache
from typing import Optional, Union
from uuid import UUID

from aioredis import Redis
from db.elastic import get_elastic
from db.redis import get_redis
from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import NotFoundError
from fastapi import Depends
from models.genre import Genre
from pydantic.json import pydantic_encoder

GENRE_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class GenreService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, genre_id: UUID) -> Genre:
        key = await self._redis_key_from_id(genre_id)
        genre = await self._get_genre_from_cache(key)
        if not genre:
            genre = await self._get_genre_from_elastic(genre_id)
            if not genre:
                return None
            await self._put_genre_to_cache(key, genre)

        return genre

    async def get_all(self) -> list[Genre]:
        key = await self._redis_key_from_all()
        genres = await self._get_genre_from_cache(key, as_list=True)
        if not genres:
            genres = await self._get_all_genres_from_elastic()
            if not genres:
                return None
            await self._put_genre_to_cache(key, genres, as_list=True)

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
        await self.redis.set(key, jsoned, expire=GENRE_CACHE_EXPIRE_IN_SECONDS)

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
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    return GenreService(redis, elastic)
