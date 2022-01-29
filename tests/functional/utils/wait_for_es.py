import asyncio
import os

from elasticsearch import AsyncElasticsearch


async def wait_for_es(es: AsyncElasticsearch, sleep_sec: float = 5) -> None:
    while not await es.ping():
        await asyncio.sleep(sleep_sec)
    await client.close()

if __name__ == '__main__':
    es_host = os.environ.get('ELASTIC_HOST') or "127.0.0.1:9200"
    client = AsyncElasticsearch(hosts=es_host)
    asyncio.run(wait_for_es(client))
