import os
from logging import config as logging_config

from pydantic import BaseSettings

from core.logger import LOGGING

# Применяем настройки логирования
logging_config.dictConfig(LOGGING)

class Settings(BaseSettings):
    PROJECT_NAME: str = 'movies'
    REDIS_HOST: str = '127.0.0.1'
    REDIS_PORT: int = 6379
    ELASTIC_HOST: str = '127.0.0.1'
    ELASTIC_PORT: int = 9200
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    FILM_CACHE_EXPIRE_IN_SECONDS: int = 60 * 5  # 5 минут
    GENRE_CACHE_EXPIRE_IN_SECONDS: int = 60 * 5  # 5 минут
    PERSON_CACHE_EXPIRE_IN_SECONDS: int = 60 * 5  # 5 минут

    class Config:
        env_file = '.env'


settings = Settings()
