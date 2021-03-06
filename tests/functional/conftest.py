import asyncio
from dataclasses import dataclass

import aiohttp
import aioredis
import pytest
from elasticsearch import AsyncElasticsearch
from multidict import CIMultiDictProxy

from .settings import test_settings

pytest_plugins = ("fixtures.film",
                  "fixtures.search",
                  "fixtures.genre",
                  "fixtures.person")

@dataclass
class HTTPResponse:
    body: dict
    headers: CIMultiDictProxy[str]
    status: int


@pytest.fixture(scope='session')
async def es_client():
    client = AsyncElasticsearch(hosts='http://' + test_settings.es_host)
    yield client
    await client.close()

@pytest.fixture(scope='session')
async def redis_client():
    client = await aioredis.create_redis_pool('redis://' + test_settings.redis_host)
    yield client
    client.close()
    await client.wait_closed()

@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope='session')
async def session(event_loop):
    session = aiohttp.ClientSession(loop=event_loop)
    yield session
    await session.close()

@pytest.fixture
def make_get_request(session):
    async def inner(method: str, params: dict = None) -> HTTPResponse:
        params = params or {}
        url = 'http://' + test_settings.service_url + '/api/v1' + method  # в боевых системах старайтесь так не делать!
        async with session.get(url, params=params) as response:
          return HTTPResponse(
            body=await response.json(),
            headers=response.headers,
            status=response.status,
          )
    return inner
