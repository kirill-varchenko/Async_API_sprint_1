import json
from http import HTTPStatus

import pytest

SEARCH_PATH = '/film/search'

VALIDATION_PARAMS = [
    ({}, 422, 'field required'),
    ({'query': 'Star Wars', 'page[size]': 0}, HTTPStatus.UNPROCESSABLE_ENTITY, 'ensure this value is greater than or equal to 1'),
    ({'query': 'Star Wars', 'page[size]': -1}, HTTPStatus.UNPROCESSABLE_ENTITY, 'ensure this value is greater than or equal to 1'),
    ({'query': 'Star Wars', 'page[size]': 'a'}, HTTPStatus.UNPROCESSABLE_ENTITY, 'value is not a valid integer'),
    ({'query': 'Star Wars', 'page[number]': 0}, HTTPStatus.UNPROCESSABLE_ENTITY, 'ensure this value is greater than or equal to 1'),
    ({'query': 'Star Wars', 'page[number]': -1}, HTTPStatus.UNPROCESSABLE_ENTITY, 'ensure this value is greater than or equal to 1'),
    ({'query': 'Star Wars', 'page[number]': 'a'}, HTTPStatus.UNPROCESSABLE_ENTITY, 'value is not a valid integer')
]

QUERY_GOOD_PARAMS = [
    ({'query': 'Star Wars'}, lambda x: x > 0),
    ({'query': 'galaxy far away'}, lambda x: x > 0),
    ({'query': 'Star Wars', 'page[size]': 10}, lambda x: x == 10),
    ({'query': 'Star Wars', 'page[number]': 1}, lambda x: x > 0)
]

@pytest.mark.asyncio
@pytest.mark.parametrize('request_data,response_status,body_msg', VALIDATION_PARAMS)
async def test_search_params_validation(make_get_request, request_data, response_status, body_msg):
    response = await make_get_request(SEARCH_PATH, request_data)

    assert response.status == response_status
    assert len(response.body) == 1
    assert response.body['detail'][0]['msg'] == body_msg

@pytest.mark.asyncio
@pytest.mark.parametrize('request_data,body_len_predicate', QUERY_GOOD_PARAMS)
async def test_search_good_params(make_get_request, request_data, body_len_predicate):
    response = await make_get_request(SEARCH_PATH, request_data)

    assert response.status == HTTPStatus.OK
    assert body_len_predicate(len(response.body))

@pytest.mark.asyncio
async def test_search_not_found(wrong_search_query, make_get_request):
    response = await make_get_request(SEARCH_PATH, {'query': wrong_search_query})

    assert response.status == HTTPStatus.NOT_FOUND
    assert len(response.body) == 1
    assert response.body == {'detail': 'films not found'}


@pytest.mark.asyncio
async def test_search_cached(fake_search_query, make_get_request, redis_client):
    await redis_client.flushall()

    # check query not return anything
    query, new_cache_key, new_cache_data = fake_search_query
    response = await make_get_request(SEARCH_PATH, {'query': query})
    assert response.status == HTTPStatus.NOT_FOUND

    # add data to cache
    new_cache_json = json.dumps(new_cache_data)
    await redis_client.set(new_cache_key, new_cache_json)

    # try again
    response = await make_get_request(SEARCH_PATH, {'query': query})
    assert response.status == HTTPStatus.OK
    assert len(response.body) == 1
    assert response.body == new_cache_data

    await redis_client.delete(new_cache_key)

