from dataclasses import asdict

from elasticsearch import Elasticsearch

from backoff import backoff
from create_es_schema.create_index import IndexCreator
from es_item import ITEM_TYPES


class Loader:
    """Загружает чанками данные в ES"""
    def __init__(self, host: str):
        self.connection = Elasticsearch([host])
        self.create_index = IndexCreator(self.connection)
        self.es = self.es_init()

    @backoff()
    def es_init(self):
        self.create_index.check_create_index()
        return self.connection

    def make_body(self, data: list[ITEM_TYPES], index: str) -> list[dict]:
        res = []
        for item in data:
            res.append({"index": {"_index": index, "_id": item.uuid}})
            res.append(asdict(item))
        return res

    @backoff()
    def load(self, data: list[ITEM_TYPES], index: str):
        body = self.make_body(data, index)
        res = self.es.bulk(body=body)
