from functools import lru_cache
from typing import Optional
from uuid import UUID

from aioredis import Redis
from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import NotFoundError
from fastapi import Depends

from db.elastic import get_elastic
from db.redis import get_redis
from models.genre import Genre

from pydantic.json import pydantic_encoder
import json


GENRE_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class GenreService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, genre_id: UUID) -> Genre:
        genre = await self._get_genre_from_cache(genre_id)
        if not genre:
            genre = await self._get_genre_from_elastic(genre_id)
            if not genre:
                return None
            await self._put_genre_to_cache(genre)

        return genre

    async def get_all(self) -> list[Genre]:
        genres = await self._get_all_genres_from_cache()
        if not genres:
            genres = await self._get_all_genres_from_elastic()
            if not genres:
                return None
            await self._put_all_genres_to_cache(genres)

        return genres

    async def _get_genre_from_elastic(self, genre_id: UUID) -> Genre:
        try:
            doc = await self.elastic.get('genres', genre_id)
            res = Genre(**doc['_source'])
        except NotFoundError:
            res = None

        return res

    async def _get_all_genres_from_elastic(self) -> list[Genre]:
        body = {
            'size' : 1000,
            'query': {
                'match_all' : {}
            }
        }
        doc = await self.elastic.search(index='genres', body=body)
        res = [Genre(**hit['_source']) for hit in doc['hits']['hits']]
        return res

    async def _get_genre_from_cache(self, genre_id: UUID) -> Genre:
        data = await self.redis.get(str(genre_id))
        if not data:
            return None

        res = Genre.parse_raw(data)
        return res

    async def _get_all_genres_from_cache(self) -> list[Genre]:
        data = await self.redis.get('genres_list')
        if not data:
            return None

        parsed = json.loads(data)
        res = [Genre(**d) for d in parsed]
        return res

    async def _put_genre_to_cache(self, genre: Genre):
        await self.redis.set(str(genre.uuid), genre.json(), expire=GENRE_CACHE_EXPIRE_IN_SECONDS)

    async def _put_all_genres_to_cache(self, genres_list: list[Genre]):
        jsoned = json.dumps(genres_list, default=pydantic_encoder)
        await self.redis.set('genres_list', jsoned, expire=GENRE_CACHE_EXPIRE_IN_SECONDS)


@lru_cache()
def get_genre_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    return GenreService(redis, elastic)
