import asyncio

import aiohttp
import environ
import pytest
from redis import Redis

env_root = environ.Path(__file__) - 3
env = environ.Env()
env_file = str(env_root.path('dev.env'))
env.read_env(env_file)


@pytest.fixture(scope='session')
async def redis_session():
    r = Redis('127.0.0.1', socket_connect_timeout=1)
    yield r


@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
async def http_session(event_loop):
    session = aiohttp.ClientSession(loop=event_loop)
    yield session
    await session.close()
