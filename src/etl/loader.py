import json
from dataclasses import asdict

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from backoff import backoff
from es_item import ITEM_TYPES


class Loader:
    def __init__(self, host: str):
        self.host = host
        self.es = self.es_init()

    @backoff()
    def es_init(self):
        return Elasticsearch([self.host])

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
