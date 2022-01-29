import asyncio
import os

import aioredis


async def wait_for_redis(host: str, sleep_sec: float = 5) -> None:
    redis = await aioredis.create_redis(host)
    while not await redis.ping():
        await asyncio.sleep(sleep_sec)
    redis.close()
    await redis.wait_closed()

if __name__ == '__main__':
    redis_host = "redis://" + (os.environ.get('REDIS_HOST') or "127.0.0.1:6379")
    asyncio.run(wait_for_redis(host=redis_host))
