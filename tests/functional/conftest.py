import aiohttp
import asyncio
import pytest
from elasticsearch import AsyncElasticsearch
import environ

env_root = environ.Path(__file__) - 3
env = environ.Env()
env_file = str(env_root.path('dev.env'))
env.read_env(env_file)

# @pytest.fixture(scope='session')
# async def es_client():
#     client = AsyncElasticsearch(hosts=env('ELASTIC_HOST')+':'+env('ELASTIC_PORT'))
#     yield client
#     await client.close()

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

