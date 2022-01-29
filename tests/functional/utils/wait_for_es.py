import asyncio

from elasticsearch import AsyncElasticsearch
from settings import test_settings


async def wait_for_es(es: AsyncElasticsearch, sleep_sec: float = 5) -> None:
    while not await es.ping():
        await asyncio.sleep(sleep_sec)
    await client.close()

if __name__ == '__main__':
    client = AsyncElasticsearch(hosts=test_settings.es_host)
    asyncio.run(wait_for_es(client))