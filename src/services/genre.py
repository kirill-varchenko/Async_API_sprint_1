from functools import lru_cache
from typing import Optional
from uuid import UUID

from core.config import settings
from db.dependens import get_cache, get_cache_creator, get_storage
from db.storage import AbstractCache, AbstractKeyCreator, AbstractStorage
from fastapi import Depends
from models.genre import Genre


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

        return genre_from_id

    async def get_all(self) -> Optional[list[Genre]]:
        key = "genres_list"
        genres = await self.cache.get_data(key, Genre, as_list=True)
        if genres:
            return genres

        genres_from_db = await self.db.get_all_from_elastic('genres', Genre)
        if not genres_from_db:
            return None
        await self.cache.put_data(key=key, data=genres_from_db, expire=settings.GENRE_CACHE_EXPIRE_IN_SECONDS, as_list=True)

        return genres_from_db


@lru_cache()
def get_genre_service(
        db: AbstractStorage = Depends(get_storage),
        cache: AbstractCache = Depends(get_cache),
        cache_creator: AbstractKeyCreator = Depends(get_cache_creator)
) -> GenreService:
    return GenreService(db, cache, cache_creator)
