from dataclasses import asdict

from elasticsearch import Elasticsearch

from backoff import backoff
from es_item import ITEM_TYPES
from config import INDEX_NAME_MOVIE, INDEX_NAME_GENRE, create_index_movies, create_index_genres, INDEX_NAME_PERSON, \
    create_index_persons

class Loader:
    """Загружает чанками данные в ES"""
    def __init__(self, host: str):
        self.host = host
        self.es = self.es_init()

    @backoff()
    def es_init(self):
        es = Elasticsearch([self.host])
        if not es.indices.exists(index=INDEX_NAME_MOVIE):
            create_index_movies(es)
        if not es.indices.exists(index=INDEX_NAME_GENRE):
            create_index_genres(es)
        if not es.indices.exists(index=INDEX_NAME_PERSON):
            create_index_persons(es)
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
