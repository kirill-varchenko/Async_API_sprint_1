from typing import Optional

from elasticsearch import Elasticsearch
from pydantic import BaseModel


class DSNSettings(BaseModel):
    dbname: str
    user: str
    host: str
    port: int
    password: Optional[str] = None


class ESSettings(BaseModel):
    host: str
    limit: int


class ProducerSettings(BaseModel):
    name: str
    state_file_path: str
    state_field: str
    limit: int
    sql: str


class EnricherSettings(BaseModel):
    name: str
    use: str
    sql: str


class MergerSettings(BaseModel):
    name: str
    use: list[str]
    sql: str


class LoaderSettings(BaseModel):
    name: str
    use: str
    index: str


class Config(BaseModel):
    dsn: DSNSettings
    es: ESSettings
    producers: list[ProducerSettings]
    enrichers: list[EnricherSettings]
    mergers: list[MergerSettings]
    loaders: list[LoaderSettings]


INDEX_NAME_MOVIE = 'movies'
INDEX_NAME_GENRE = 'genres'
INDEX_NAME_PERSON = 'persons'


def create_index_movies(es: Elasticsearch):
    index_movies = {
        "settings": {
            "refresh_interval":"1s",
            "analysis":{
              "filter":{
                "english_stop":{
                  "type":"stop",
                  "stopwords":"_english_"
                },
                "english_stemmer":{
                  "type":"stemmer",
                  "language":"english"
                },
                "english_possessive_stemmer":{
                  "type":"stemmer",
                  "language":"possessive_english"
                },
                "russian_stop":{
                  "type":"stop",
                  "stopwords":"_russian_"
                },
                "russian_stemmer":{
                  "type":"stemmer",
                  "language":"russian"
                }
              },
              "analyzer":{
                "ru_en":{
                  "tokenizer":"standard",
                  "filter":[
                    "lowercase",
                    "english_stop",
                    "english_stemmer",
                    "english_possessive_stemmer",
                    "russian_stop",
                    "russian_stemmer"
                  ]
                }
              }
            }
        },
        "mappings":{
        "dynamic":"strict",
        "properties":{
          "uuid":{
            "type":"keyword"
          },
          "imdb_rating":{
            "type":"float"
          },
          "genres_names":{
            "type":"text"
          },
          "genre":{
            "type":"nested",
            "dynamic":"strict",
            "properties":{
              "uuid":{
                "type":"keyword"
              },
              "name":{
                "type":"text",
                "analyzer":"ru_en"
              }
            }
          },
          "title":{
            "type":"text",
            "analyzer":"ru_en",
            "fields":{
              "raw":{
                "type":"keyword"
              }
            }
          },
          "description":{
            "type":"text",
            "analyzer":"ru_en"
          },
          "directors_names":{
            "type":"text",
            "analyzer":"ru_en"
          },
          "actors_names":{
            "type":"text",
            "analyzer":"ru_en"
          },
          "writers_names":{
            "type":"text",
            "analyzer":"ru_en"
          },
          "actors":{
            "type":"nested",
            "dynamic":"strict",
            "properties":{
              "uuid":{
                "type":"keyword"
              },
              "full_name":{
                "type":"text",
                "analyzer":"ru_en"
              }
            }
          },
          "writers":{
            "type":"nested",
            "dynamic":"strict",
            "properties":{
              "uuid":{
                "type":"keyword"
              },
              "full_name":{
                "type":"text",
                "analyzer":"ru_en"
              }
            }
          },
          "directors":{
            "type":"nested",
            "dynamic":"strict",
            "properties":{
              "uuid":{
                "type":"keyword"
              },
              "full_name":{
                "type":"text",
                "analyzer":"ru_en"
              }
            }
          }
        }
        }
        }

    es.indices.create(index=INDEX_NAME_MOVIE, body=index_movies)


def create_index_genres(es: Elasticsearch):
    index_genres = {
        "settings": {
        "refresh_interval": "1s",
        "analysis": {
          "filter": {
            "english_stop": {
              "type":       "stop",
              "stopwords":  "_english_"
            },
            "english_stemmer": {
              "type": "stemmer",
              "language": "english"
            },
            "english_possessive_stemmer": {
              "type": "stemmer",
              "language": "possessive_english"
            },
            "russian_stop": {
              "type":       "stop",
              "stopwords":  "_russian_"
            },
            "russian_stemmer": {
              "type": "stemmer",
              "language": "russian"
            }
          },
          "analyzer": {
            "ru_en": {
              "tokenizer": "standard",
              "filter": [
                "lowercase",
                "english_stop",
                "english_stemmer",
                "english_possessive_stemmer",
                "russian_stop",
                "russian_stemmer"
              ]
            }
          }
        }
        },
        "mappings": {
        "dynamic": "strict",
        "properties": {
          "uuid": {
            "type": "keyword"
          },
          "name": {
            "type": "keyword"
          }
        }
        }
        }

    es.indices.create(index=INDEX_NAME_GENRE, body=index_genres)


def create_index_persons(es: Elasticsearch):
    index_persons = {
        "settings": {
        "refresh_interval": "1s",
        "analysis": {
          "filter": {
            "english_stop": {
              "type":       "stop",
              "stopwords":  "_english_"
            },
            "english_stemmer": {
              "type": "stemmer",
              "language": "english"
            },
            "english_possessive_stemmer": {
              "type": "stemmer",
              "language": "possessive_english"
            },
            "russian_stop": {
              "type":       "stop",
              "stopwords":  "_russian_"
            },
            "russian_stemmer": {
              "type": "stemmer",
              "language": "russian"
            }
          },
          "analyzer": {
            "ru_en": {
              "tokenizer": "standard",
              "filter": [
                "lowercase",
                "english_stop",
                "english_stemmer",
                "english_possessive_stemmer",
                "russian_stop",
                "russian_stemmer"
              ]
            }
          }
        }
        },
        "mappings": {
        "dynamic": "strict",
        "properties": {
          "uuid": {
            "type": "keyword"
          },
          "full_name": {
            "type": "text",
            "analyzer": "ru_en",
            "fields": {
              "raw": {
                "type":  "keyword"
              }
            }
          }
        }
        }
        }

    es.indices.create(index=INDEX_NAME_PERSON, body=index_persons)
