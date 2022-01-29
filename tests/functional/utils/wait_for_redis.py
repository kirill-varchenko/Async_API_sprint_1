import asyncio
import os
import sys

import aioredis


async def wait_for_redis(host: str,
                      start_sleep_time: float = 0.1,
                      factor: float = 2,
                      border_sleep_time: float = 10,
                      max_tries: int = 20
                      ) -> int:
    """Функция для ожидания готовности Redis.
    Parameters
    ----------
    host : str
        путь к Redis
    start_sleep_time : float, optional
        начальное время повтора, by default 0.1
    factor : float, optional
        во сколько раз нужно увеличить время ожидания, by default 2
    border_sleep_time : float, optional
        граничное время ожидания, by default 10
    max_tries : int, optional
        Максимальное количество попыток, by default 20
    """
    redis = await aioredis.create_redis(host)
    t = start_sleep_time
    n = 0
    exit_code = 1 # failure
    while n < max_tries:
        n += 1
        if await redis.ping():
            exit_code = 0 # success
            break
        else:
            await asyncio.sleep(t)
            t = t * factor if t < border_sleep_time else border_sleep_time

    redis.close()
    await redis.wait_closed()
    return exit_code

if __name__ == '__main__':
    redis_host = "redis://" + (os.environ.get('REDIS_HOST') or "127.0.0.1:6379")
    exit_code = asyncio.run(wait_for_redis(host=redis_host))
    # Выходим с кодом, чтобы прервать цепочку вызовов через && при неудачном подключении
    sys.exit(exit_code)
