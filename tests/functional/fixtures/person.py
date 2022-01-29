import json
import random
import string
import uuid

import pytest


@pytest.fixture
def fake_person_data():
    new_uuid = str(uuid.uuid4())
    random_name = ''.join(random.choices(string.ascii_uppercase, k=20))
    new_data = {"uuid":new_uuid,
                "full_name": random_name,
                "role":"director, writer",
                "film_ids": ["bfe61bd9-5dfd-41ca-80ae-8eca998bc29d"]}
    return new_data


@pytest.fixture
def real_person_data():
    with open('testdata/real_persons.json', 'r') as fi:
        real_person_data = json.load(fi)
    return real_person_data
