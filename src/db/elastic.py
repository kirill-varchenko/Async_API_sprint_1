from typing import Optional
from uuid import UUID

from elasticsearch import AsyncElasticsearch, NotFoundError

from api.v1 import models
from db.storage import AbstractStorage

es: Optional[AsyncElasticsearch] = None


class ElasticStorage(AbstractStorage):
    def __init__(self):
        self.elastic = es

    async def get_data_by_id(self, index: str, id: UUID, model: models) -> Optional[models.BaseModel]:
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

    async def get_person_films_from_elastic(self, index: str, person_id: UUID, model) -> list[models.BaseModel]:
        body = {
            "_source": [
                "uuid",
                "title",
                "imdb_rating",
                "actors",
                "writers",
                "directors",
            ],
            "query": {
                "bool": {
                    "should": [
                        {
                            "nested": {
                                "path": "actors",
                                "query": {
                                    "bool": {
                                        "should": [{"term": {"actors.uuid": person_id}}]
                                    }
                                },
                            }
                        },
                        {
                            "nested": {
                                "path": "writers",
                                "query": {
                                    "bool": {
                                        "should": [
                                            {"term": {"writers.uuid": person_id}}
                                        ]
                                    }
                                },
                            }
                        },
                        {
                            "nested": {
                                "path": "directors",
                                "query": {
                                    "bool": {
                                        "should": [
                                            {"term": {"directors.uuid": person_id}}
                                        ]
                                    }
                                },
                            }
                        },
                    ]
                }
            },
        }
        doc = await self.elastic.search(index=index, body=body)
        films = [model(**hit["_source"]) for hit in doc["hits"]["hits"]]
        return films

    async def get_person_search_from_elastic(
            self, index: str, query: str, model, parameters: dict = None
    ) -> list[models.BaseModel]:
        if query:
            body = {"query": {"match": {"full_name": {"query": query}}}}
        else:
            body = {"query": {"match_all": {}}}
        additional_params = {
            "from": (parameters["page_number"] - 1) * parameters["page_size"],
            "size": parameters["page_size"],
        }
        if parameters["sort"] == "full_name":
            additional_params.update({"sort": [{"full_name.raw": {"order": "asc"}}]})
        elif parameters["sort"] == "-full_name":
            additional_params.update({"sort": [{"full_name.raw": {"order": "desc"}}]})
        body.update(additional_params)

        doc = await self.elastic.search(index=index, body=body)
        persons = [model(**hit["_source"]) for hit in doc["hits"]["hits"]]
        return persons

    async def get_all_from_elastic(self, index: str, model) -> list[models.BaseModel]:
        body = {"size": 1000, "query": {"match_all": {}}}
        doc = await self.elastic.search(index=index, body=body)
        res = [model(**hit["_source"]) for hit in doc["hits"]["hits"]]
        return res
