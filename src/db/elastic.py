from typing import Optional
from uuid import UUID

from elasticsearch import AsyncElasticsearch, NotFoundError

from api.v1 import models
from db.storage import AbstractConnection, AbstractStorage, AbstractStorageRequest

es: Optional[AsyncElasticsearch] = None


async def get_elastic() -> AsyncElasticsearch:
    return es

#
# class ElasticConnection(AbstractConnection):
#     def __init__(self, es: Optional[AsyncElasticsearch] = None):
#         self.es = es
#
#     async def get_connection(self) -> AsyncElasticsearch:
#         return self.es
#


class ElasticStorage(AbstractStorage):
    def __init__(self):
        self.elastic = es

    async def get_data_by_id(self, index: str, id: UUID, model: models, parameters: dict = None) -> Optional[models.BaseModel]:
        try:
            doc = await self.elastic.get(index, id)
            return model(**doc["_source"])
        except NotFoundError:
            return None

    async def get_data_list_by_id(
            self, index: str, filter_genre: UUID, model: models, parameters: dict = None
    ) -> Optional[list[models.BaseModel]]:

        if filter_genre:
            body = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "nested": {
                                    "path": "genre",
                                    "query": {
                                        "bool": {
                                            "should": [
                                                {"term": {"genre.uuid": filter_genre}}
                                            ]
                                        }
                                    },
                                }
                            }
                        ]
                    }
                }
            }
        else:
            body = {"query": {"match_all": {}}}
        additional_params = {
            "from": (parameters["page_number"] - 1) * parameters["page_size"],
            "size": parameters["page_size"],
        }
        if parameters["sort"] == "imdb_rating":
            additional_params.update({"sort": [{"imdb_rating": {"order": "asc"}}]})
        elif parameters["sort"] == "-imdb_rating":
            additional_params.update({"sort": [{"imdb_rating": {"order": "desc"}}]})
        body.update(additional_params)

        doc = await self.elastic.search(index=index, body=body)
        films = [model(**hit["_source"]) for hit in doc["hits"]["hits"]]
        return films

    async def get_data_by_query(
            self, index: str, query: str, model, parameters: dict = None
    ) -> Optional[list[models.BaseModel]]:
        if query:
            body = {
                "query": {
                    "bool": {
                        "should": [
                            {"match": {"title": query}},
                            {"match": {"description": query}},
                        ]
                    }
                }
            }
        else:
            body = {"query": {"match_all": {}}}
        additional_params = {
            "from": (parameters["page_number"] - 1) * parameters["page_size"],
            "size": parameters["page_size"],
        }
        if parameters["sort"] == "imdb_rating":
            additional_params.update({"sort": [{"imdb_rating": {"order": "asc"}}]})
        elif parameters["sort"] == "-imdb_rating":
            additional_params.update({"sort": [{"imdb_rating": {"order": "desc"}}]})
        body.update(additional_params)

        doc = await self.elastic.search(index=index, body=body)
        films = [model(**hit["_source"]) for hit in doc["hits"]["hits"]]
        return films

# class ElasticRequesterId(AbstractStorageRequest):
#     def __init__(self):
#         self.elastic = es
#
#     async def request(self, index: str, id: UUID, model: models, parameters: dict = None) -> Optional[models.BaseModel]:
#         try:
#             doc = await self.elastic.get(index, id)
#             return model(**doc["_source"])
#         except NotFoundError:
#             return None

#
# class ElasticRequesterFilmList(AbstractStorageRequest):
#     def __init__(self):
#         self.elastic = es
#
#     async def get_data_list_by_id(
#             self, index: str, filter_genre: UUID, model: models, parameters: dict = None
#     ) -> Optional[list[models.BaseModel]]:
#         if filter_genre:
#             body = {
#                 "query": {
#                     "bool": {
#                         "must": [
#                             {
#                                 "nested": {
#                                     "path": "genre",
#                                     "query": {
#                                         "bool": {
#                                             "should": [
#                                                 {"term": {"genre.uuid": filter_genre}}
#                                             ]
#                                         }
#                                     },
#                                 }
#                             }
#                         ]
#                     }
#                 }
#             }
#         else:
#             body = {"query": {"match_all": {}}}
#         additional_params = {
#             "from": (parameters["page_number"] - 1) * parameters["page_size"],
#             "size": parameters["page_size"],
#         }
#         if parameters["sort"] == "imdb_rating":
#             additional_params.update({"sort": [{"imdb_rating": {"order": "asc"}}]})
#         elif parameters["sort"] == "-imdb_rating":
#             additional_params.update({"sort": [{"imdb_rating": {"order": "desc"}}]})
#         body.update(additional_params)
#
#         doc = await self.elastic.search(index=index, body=body)
#         films = [model(**hit["_source"]) for hit in doc["hits"]["hits"]]
#         return films
#
#
