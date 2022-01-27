from functools import lru_cache

from db.elastic import ElasticStorage
from db.redis import RedisStorage, RedisCreator
from db.storage import AbstractStorage, AbstractCache, AbstractKeyCreator


async def get_storage() -> AbstractStorage:
    db = ElasticStorage()
    return db


async def get_cache() -> AbstractCache:
    cache = RedisStorage()
    return cache


async def get_cache_creator() -> AbstractKeyCreator:
    cache_creator = RedisCreator()
    return cache_creator

