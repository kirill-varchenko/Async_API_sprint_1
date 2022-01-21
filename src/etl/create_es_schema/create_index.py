import json

from config import config


class IndexCreator:
    def __init__(self, connection):
        self.es = connection

    def check_create_index(self):
        for loader in config.loaders:
            if not self.es.indices.exists(index=loader.index):
                body = json.loads(loader.index)
                self.es.indices.create(index=loader.index, body=body)
