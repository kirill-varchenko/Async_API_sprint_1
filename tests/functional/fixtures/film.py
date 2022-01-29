import json
import uuid

import pytest


@pytest.fixture
def fake_film_data():
    new_uuid = str(uuid.uuid4())
    new_data= {'uuid': new_uuid, 'title': 'Test film', 'imdb_rating': 1.1,
               'description': 'Test film description', 'genre': [],
               'actors': [], 'writers': [], 'directors': []}
    return new_data


@pytest.fixture
def real_film_data():
    with open('testdata/real_films.json', 'r') as fi:
        real_film_data = json.load(fi)
    for data in real_film_data:
        yield data
