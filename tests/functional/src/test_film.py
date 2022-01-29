import json
from http import HTTPStatus

import pytest

FILM_PATH = '/film'

VALIDATION_PARAMS = [
    ({'page[size]': 0}, HTTPStatus.UNPROCESSABLE_ENTITY, 'ensure this value is greater than or equal to 1'),
    ({'page[size]': -1}, HTTPStatus.UNPROCESSABLE_ENTITY, 'ensure this value is greater than or equal to 1'),
    ({'page[size]': 'a'}, HTTPStatus.UNPROCESSABLE_ENTITY, 'value is not a valid integer'),
    ({'page[number]': 0}, HTTPStatus.UNPROCESSABLE_ENTITY, 'ensure this value is greater than or equal to 1'),
    ({'page[number]': -1}, HTTPStatus.UNPROCESSABLE_ENTITY, 'ensure this value is greater than or equal to 1'),
    ({'page[number]': 'a'}, HTTPStatus.UNPROCESSABLE_ENTITY, 'value is not a valid integer')
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

    assert response.status == HTTPStatus.UNPROCESSABLE_ENTITY
    assert len(response.body) == 1
    assert response.body['detail'][0]['msg'] == 'value is not a valid uuid'

### Проверка поиска конкретного фильма ###
@pytest.mark.asyncio
async def test_search_for_film(real_film_data, make_get_request):
    real_uuid = real_film_data.get('uuid')
    response = await make_get_request(f'{FILM_PATH}/{real_uuid}', {})

    assert response.status == HTTPStatus.OK
    assert response.body.get('title') == real_film_data.get('title')

### Вывести все фильмы ###
@pytest.mark.asyncio
async def test_list_films(make_get_request):
    response = await make_get_request(f'{FILM_PATH}/', {'page[size]': 50,
                                                        'page[number]': 1})

    assert response.status == HTTPStatus.OK
    assert len(response.body) == 50

@pytest.mark.asyncio
async def test_film_cached(fake_film_data, make_get_request, redis_client):
    await redis_client.flushall()

    # check query not return anything
    new_uuid = fake_film_data.get('uuid')
    response = await make_get_request(f'{FILM_PATH}/{new_uuid}', {})
    assert response.status == HTTPStatus.NOT_FOUND

    # add data to cache
    new_cache_json = json.dumps(fake_film_data)
    await redis_client.set(new_uuid, new_cache_json)

    # try again
    response = await make_get_request(f'{FILM_PATH}/{new_uuid}', {})
    assert response.status == HTTPStatus.OK
    assert len(response.body) > 0
    assert response.body == fake_film_data

    await redis_client.delete(new_uuid)
