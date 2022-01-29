import json
from http import HTTPStatus

import pytest

GENRE_PATH = '/genre/'

@pytest.mark.asyncio
async def test_all_genres(real_genre_data, make_get_request):
    response = await make_get_request(GENRE_PATH, {})
    assert response.status == HTTPStatus.OK
    assert len(response.body) == len(real_genre_data)
    assert response.body == real_genre_data

@pytest.mark.asyncio
async def test_genre_by_uuid(real_genre_data, make_get_request):
    genre = real_genre_data[0]
    response = await make_get_request(GENRE_PATH + genre.get('uuid'), {})
    assert response.status == HTTPStatus.OK
    assert len(response.body) == 2
    assert response.body == genre

@pytest.mark.asyncio
async def test_genre_by_uuid_absent(fake_genre_data, make_get_request):
    response = await make_get_request(GENRE_PATH + fake_genre_data.get('uuid'), {})
    assert response.status == HTTPStatus.NOT_FOUND
    assert len(response.body) == 1
    assert response.body == {'detail': 'genre not found'}

@pytest.mark.asyncio
async def test_genre_by_uuid_incorrect(make_get_request):
    response = await make_get_request(GENRE_PATH + '111', {})
    assert response.status == HTTPStatus.UNPROCESSABLE_ENTITY
    assert len(response.body) == 1
    assert response.body == {"detail": [{"loc": ["path", "genre_id"], "msg": "value is not a valid uuid", "type": "type_error.uuid"}]}

@pytest.mark.asyncio
async def test_redis(fake_genre_data, make_get_request, redis_client):
    await redis_client.flushall()
    await redis_client.set(fake_genre_data.get('uuid'), json.dumps(fake_genre_data))
    response = await make_get_request(GENRE_PATH + fake_genre_data.get('uuid'), {})
    assert response.body == fake_genre_data
    await redis_client.delete(fake_genre_data.get('uuid'))
