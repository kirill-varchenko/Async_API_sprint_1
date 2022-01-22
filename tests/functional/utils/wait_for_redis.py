from time import sleep

from aioredis import Redis


def wait_for_redis(redis: Redis, sleep_sec: float = 5) -> None:
    while not redis.ping():
        sleep(sleep_sec)

