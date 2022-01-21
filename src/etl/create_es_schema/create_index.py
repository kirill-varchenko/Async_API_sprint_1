import json

from elasticsearch import Elasticsearch
from config import config


class CreateIndex:
    def __init__(self, es_host):
        self.es = Elasticsearch(es_host)

    def create_index_movies(self):
        if not self.es.indices.exists(index=config.loaders[0].index):
            index_movies = json.loads('film_schema')
            self.es.indices.create(index=config.loaders[0].index, body=index_movies)

    def create_index_persons(self):
        if not self.es.indices.exists(index=config.loaders[1].index):
            index_persons = json.loads('person_schema')
            self.es.indices.create(index=config.loaders[1].index, body=index_persons)

    def create_index_genres(self):
        if not self.es.indices.exists(index=config.loaders[2].index):
            index_genres = json.loads('genre_schema')
            self.es.indices.create(index=config.loaders[2].index, body=index_genres)
