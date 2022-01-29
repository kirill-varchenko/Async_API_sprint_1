import json

import pytest

FILM_PATH = '/film'

VALIDATION_PARAMS = [
    ({'page[size]': 0}, 422, 'ensure this value is greater than or equal to 1'),
    ({'page[size]': -1}, 422, 'ensure this value is greater than or equal to 1'),
    ({'page[size]': 'a'}, 422, 'value is not a valid integer'),
    ({'page[number]': 0}, 422, 'ensure this value is greater than or equal to 1'),
    ({'page[number]': -1}, 422, 'ensure this value is greater than or equal to 1'),
    ({'page[number]': 'a'}, 422, 'value is not a valid integer')
]

### Проверка валидации параметров в film ###
@pytest.mark.asyncio
@pytest.mark.parametrize('request_data,response_status,body_msg', VALIDATION_PARAMS)
async def test_film_params_validation(make_get_request, request_data, response_status, body_msg):
    response = await make_get_request(FILM_PATH, request_data)

    assert response.status == response_status
    assert len(response.body) == 1
    assert response.body['detail'][0]['msg'] == body_msg


### Проверка валидации параметров поиска фильма по айди ###
@pytest.mark.asyncio
async def test_search_for_film_invalid_id(make_get_request):
    response = await make_get_request(f'{FILM_PATH}/test', {})

    assert response.status == 422
    assert len(response.body) == 1
    assert response.body['detail'][0]['msg'] == 'value is not a valid uuid'

### Проверка поиска конкретного фильма ###
@pytest.mark.asyncio
async def test_search_for_film(make_get_request):
    response = await make_get_request(f'{FILM_PATH}/e7e6d147-cc10-406c-a7a2-5e0be2231327', {})

    assert response.status == 200
    assert response.body.get('title') == 'Shooting Star'

### Вывести все фильмы ###
@pytest.mark.asyncio
async def test_list_films(make_get_request):
    response = await make_get_request(f'{FILM_PATH}/', {'page[size]': 50,
                                                        'page[number]': 1})

    assert response.status == 200
    assert len(response.body) == 50

@pytest.mark.asyncio
async def test_film_cached(make_get_request, redis_client):
    await redis_client.flushall()

    # check query not return anything
    new_uuid = 'a5bd690c-121b-4e5e-a4fc-21c2dc868d4f'
    response = await make_get_request(f'{FILM_PATH}/{new_uuid}', {})
    assert response.status == 404

    # add data to cache
    new_cache_data= {'uuid': new_uuid, 'title': 'Test film', 'imdb_rating': 1.1,
                     'description': 'Test film description', 'genre': [],
                     'actors': [], 'writers': [], 'directors': []}
    new_cache_json = json.dumps(new_cache_data)
    await redis_client.set(new_uuid, new_cache_json)

    # try again
    response = await make_get_request(f'{FILM_PATH}/{new_uuid}', {})
    assert response.status == 200
    assert len(response.body) > 0
    assert response.body == new_cache_data

    await redis_client.delete(new_uuid)
