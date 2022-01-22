from time import sleep

from elasticsearch import AsyncElasticsearch


def wait_for_es(es: AsyncElasticsearch, sleep_sec: float = 5) -> None:
    while not es.ping():
        sleep(sleep_sec)
