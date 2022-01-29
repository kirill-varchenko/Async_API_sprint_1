import json
from http import HTTPStatus

import pytest

PERSON_PATH = '/person/'

VALIDATION_PARAMS = [
    ({'page[size]': 0}, 'ensure this value is greater than or equal to 1'),
    ({'page[size]': -1}, 'ensure this value is greater than or equal to 1'),
    ({'page[size]': 'a'}, 'value is not a valid integer'),
    ({'page[number]': 0}, 'ensure this value is greater than or equal to 1'),
    ({'page[number]': -1}, 'ensure this value is greater than or equal to 1'),
    ({'page[number]': 'a'}, 'value is not a valid integer')
]

### Проверка валидации параметров в film ###
@pytest.mark.asyncio
@pytest.mark.parametrize('request_data,body_msg', VALIDATION_PARAMS)
async def test_person_params_validation(real_person_data, make_get_request, request_data, body_msg):
    real_person_name = real_person_data[0]['full_name']
    response = await make_get_request(PERSON_PATH + 'search?', request_data | {'query': real_person_name})

    assert response.status == HTTPStatus.UNPROCESSABLE_ENTITY
    assert len(response.body) == 1
    assert response.body['detail'][0]['msg'] == body_msg

@pytest.mark.asyncio
async def test_list_persons(make_get_request):
    response = await make_get_request(PERSON_PATH + 'search', {'page[size]': 50,
                                                                'page[number]': 1,
                                                                'query': ''})

    assert response.status == HTTPStatus.OK
    assert len(response.body) == 50

@pytest.mark.asyncio
async def test_person_search(real_person_data, make_get_request):
    person = real_person_data[0]
    response = await make_get_request(PERSON_PATH + 'search', {'query': person.get('full_name')})
    assert response.status == HTTPStatus.OK
    assert len(response.body) > 0
    assert person.get('full_name') in [p['full_name'] for p in response.body]

@pytest.mark.asyncio
async def test_person_search_absent(fake_person_data, make_get_request):
    person_name = fake_person_data.get('full_name')
    response = await make_get_request(PERSON_PATH + 'search', {'query': person_name})
    assert response.status == HTTPStatus.NOT_FOUND
    assert len(response.body) == 1
    assert response.body == {'detail': 'person not found'}

@pytest.mark.asyncio
async def test_person_by_uuid(real_person_data, make_get_request):
    person = real_person_data[0]
    response = await make_get_request(PERSON_PATH + person.get('uuid'), {})
    assert response.status == HTTPStatus.OK
    assert len(response.body) == 4
    assert response.body == person

@pytest.mark.asyncio
async def test_person_by_uuid_film(real_person_data, make_get_request):
    person = real_person_data[0]
    response = await make_get_request(PERSON_PATH + person.get('uuid') + '/film', {})
    assert response.status == HTTPStatus.OK
    assert len(response.body) == len(person.get('film_ids'))
    assert {f['uuid'] for f in response.body} == set(person.get('film_ids'))

@pytest.mark.asyncio
async def test_person_by_uuid_absent(fake_person_data, make_get_request):
    response = await make_get_request(PERSON_PATH + fake_person_data.get('uuid'), {})
    assert response.status == HTTPStatus.NOT_FOUND
    assert len(response.body) == 1
    assert response.body == {'detail': 'person not found'}

@pytest.mark.asyncio
async def test_person_by_uuid_incorrect(make_get_request):
    response = await make_get_request(PERSON_PATH + '111', {})
    assert response.status == HTTPStatus.UNPROCESSABLE_ENTITY
    assert len(response.body) == 1
    assert response.body == {"detail": [{"loc": ["path", "person_id"], "msg": "value is not a valid uuid", "type": "type_error.uuid"}]}


@pytest.mark.asyncio
async def test_redis(fake_person_data, redis_client, make_get_request):
    await redis_client.flushall()
    await redis_client.set(fake_person_data.get('uuid'), json.dumps(fake_person_data))
    response = await make_get_request(PERSON_PATH + fake_person_data.get('uuid'))
    assert response.body == fake_person_data
    await redis_client.delete(fake_person_data.get('uuid'))
