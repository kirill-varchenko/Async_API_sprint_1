import uuid

import pytest


@pytest.fixture
def wrong_search_query():
    return 'randomwrongquery'

@pytest.fixture
def fake_search_query():
    query = 'newquery'
    new_cache_key = f"film-search-{query}-None-50-1"
    new_cache_data= [{"uuid": str(uuid.uuid4()),
                      "title":"newquery",
                      "imdb_rating":1.1}]
    return query, new_cache_key, new_cache_data
