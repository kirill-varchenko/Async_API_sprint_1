import json
from typing import Optional, Union
from uuid import UUID

import aioredis
from aioredis import Redis
from pydantic.json import pydantic_encoder

from core.config import settings
from db.storage import AbstractConnection, AbstractCache, AbstractKeyCreator
from api.v1 import models

redis: Optional[Redis] = None

# Функция понадобится при внедрении зависимостей
async def get_redis() -> Redis:
    return redis


class RedisConnection(AbstractConnection):
    # def __init__(self, redis: Optional[Redis] = None):
    #     self.redis = redis

    async def get_connection(self) -> Redis:
        redis_connection = await aioredis.create_redis_pool((settings.REDIS_HOST, settings.REDIS_PORT), minsize=10, maxsize=20)
        return redis_connection


class RedisCreator(AbstractKeyCreator):
    # def __init__(self, id, query, list_parameters):
    #     self.id = id
    #     self.query = query
    #     self.list_parameters = list_parameters

    async def get_key_from_id(self, pk: UUID) -> str:
        return str(pk)

    async def redis_key_from_search(self, query, list_parameters) -> str:
        return f"film-search-{query}-{list_parameters['sort']}-{list_parameters['page_size']}-{list_parameters['page_number']}"
    #
    # async def redis_key_from_list(self, filter_genre, list_parameters) -> str:
    #     return f"film-list-{filter_genre}-{list_parameters['sort']}-{list_parameters['page_size']}-{list_parameters['page_number']}"
    #
    #
    #
    # async def redis_key_from_id(self, person_id: UUID) -> str:
    #     return str(person_id)
    #
    # async def redis_key_from_search(self, query, list_parameters) -> str:
    #     return f"person-search-{query}-{list_parameters['sort']}-{list_parameters['page_size']}-{list_parameters['page_number']}"
    #
    # async def redis_key_from_films_list(self, person_id: UUID) -> str:
    #     return f"person-films-{person_id}"
    #
    #
    #
    # async def _redis_key_from_id(self, genre_id: UUID) -> str:
    #     return str(genre_id)
    #
    # async def _redis_key_from_all(self) -> str:
    #     return "genres_list"


class RedisStorage(AbstractCache):
    def __init__(self):
        self.redis = redis

    async def get_data(self, key: str, model, as_list: bool = False) -> Optional[models.BaseModel]:
        data = await self.redis.get(key)
        if not data:
            return None

        if as_list:
            parsed = json.loads(data)
            res = [model(**d) for d in parsed]
        else:
            res = model.parse_raw(data)

        return res

    async def put_data(
            self, key: str, data: Union[models.BaseModel, list[models.BaseModel]], as_list: bool = False, expire: int = 300
    ):
        if as_list:
            jsoned = json.dumps(data, default=pydantic_encoder)
        else:
            jsoned = data.json()
        await self.redis.set(key, jsoned, expire=expire)

    # class RedisRequest(AbstractStorageRequest):
#     def __init__(self, key: str, model, as_list: bool = False):
#         self.redis = Connection(RedisConnection()).connection
#         self.key = key
#         self.model = model
#         self.as_list = as_list
#
#     async def request(self):
#         data = await self.redis.get(self.key)
#         if not data:
#             return None
#
#         if self.as_list:
#             parsed = json.loads(data)
#             res = [self.model(**d) for d in parsed]
#         else:
#             res = self.model.parse_raw(data)
#
#         return res











# class StoragePut:
#     def __init__(self, storage: AbstractStoragePut):
#         storage.put_data()
#
#
# class RedisPutParams(AbstractStoragePut):
#     def __init__(self, storage_request: AbstractStorageRequest):
#         self.storage_request = storage_request
#
#     async def put_data(self):
#         await self.storage_request.request()
#
#
# class RedisPutRequest(AbstractStorageRequest):
#     def __init__(self, key: str, data, as_list: bool = False, expire: int = 300):
#         self.redis = Connection(RedisConnection()).connection
#         self.key = key
#         self.data = data
#         self.as_list = as_list
#         self.expire = expire
#
#     async def request(self):
#         if self.as_list:
#             jsoned = json.dumps(self.data, default=pydantic_encoder)
#         else:
#             jsoned = self.data.json()
#         await self.redis.set(self.key, jsoned, expire=self.expire)
