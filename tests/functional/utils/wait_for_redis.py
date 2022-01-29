import asyncio

import aioredis
from settings import test_settings


async def wait_for_redis(sleep_sec: float = 5) -> None:
    redis = await aioredis.create_redis_pool(test_settings.redis_host)
    while not await redis.ping():
        await asyncio.sleep(sleep_sec)
    redis.close()
    await redis.wait_closed()

if __name__ == '__main__':
    asyncio.run(wait_for_redis())
