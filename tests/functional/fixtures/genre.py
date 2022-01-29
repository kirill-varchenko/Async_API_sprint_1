import json
import uuid

import pytest


@pytest.fixture
def fake_genre_data():
    new_uuid = str(uuid.uuid4())
    new_data = {'uuid': new_uuid,
                'name': 'Unknown genre'}
    return new_data


@pytest.fixture
def real_genre_data():
    with open('testdata/real_genres.json', 'r') as fi:
        real_genre_data = json.load(fi)
    return real_genre_data
