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


class RedisCreator(AbstractKeyCreator):
    # def __init__(self, id, query, list_parameters):
    #     self.id = id
    #     self.query = query
    #     self.list_parameters = list_parameters

    async def get_key_from_id(self, pk: UUID) -> str:
        return str(pk)

    async def get_key_from_search(self, name_model: str, query: str, list_parameters: dict) -> str:
        return f"{name_model}-search-{query}-{list_parameters['sort']}-{list_parameters['page_size']}-{list_parameters['page_number']}"

    async def get_key_from_films_list(self, name_model: str, pk: UUID) -> str:
        return f"{name_model}-films-{pk}"
    #
    # async def redis_key_from_list(self, filter_genre, list_parameters) -> str:
    #     return f"film-list-{filter_genre}-{list_parameters['sort']}-{list_parameters['page_size']}-{list_parameters['page_number']}"
    #
    #
    #
    # async def redis_key_from_search(self, query, list_parameters) -> str:
    #     return f"person-search-{query}-{list_parameters['sort']}-{list_parameters['page_size']}-{list_parameters['page_number']}"
    #

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
