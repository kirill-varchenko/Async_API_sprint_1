from dataclasses import dataclass

import pytest
from multidict import CIMultiDictProxy

tasks = [('UUID', {'UUID': '120a21cf-9097-479e-904a-13dd7198c1dd'},
          {"uuid": "120a21cf-9097-479e-904a-13dd7198c1dd", "name": "Adventure"}, 200, 2, 'Query for UUID'),
         ('All', {}, [{"uuid": "0b105f87-e0a5-45dc-8ce7-f8632088f390", "name": "Western"},
                      {"uuid": "120a21cf-9097-479e-904a-13dd7198c1dd", "name": "Adventure"},
                      {"uuid": "1cacff68-643e-4ddd-8f57-84b62538081a", "name": "Drama"},
                      {"uuid": "237fd1e4-c98e-454e-aa13-8a13fb7547b5", "name": "Romance"},
                      {"uuid": "2f89e116-4827-4ff4-853c-b6e058f71e31", "name": "Sport"},
                      {"uuid": "31cabbb5-6389-45c6-9b48-f7f173f6c40f", "name": "Talk-Show"},
                      {"uuid": "3d8d9bf5-0d90-4353-88ba-4ccc5d2c07ff", "name": "Action"},
                      {"uuid": "526769d7-df18-4661-9aa6-49ed24e9dfd8", "name": "Thriller"},
                      {"uuid": "5373d043-3f41-4ea8-9947-4b746c601bbd", "name": "Comedy"},
                      {"uuid": "55c723c1-6d90-4a04-a44b-e9792040251a", "name": "Family"},
                      {"uuid": "56b541ab-4d66-4021-8708-397762bff2d4", "name": "Music"},
                      {"uuid": "63c24835-34d3-4279-8d81-3c5f4ddb0cdc", "name": "Crime"},
                      {"uuid": "6a0a479b-cfec-41ac-b520-41b2b007b611", "name": "Animation"},
                      {"uuid": "6c162475-c7ed-4461-9184-001ef3d9f26e", "name": "Sci-Fi"},
                      {"uuid": "6d141ad2-d407-4252-bda4-95590aaf062a", "name": "Documentary"},
                      {"uuid": "9c91a5b2-eb70-4889-8581-ebe427370edd", "name": "Musical"},
                      {"uuid": "a886d0ec-c3f3-4b16-b973-dedcf5bfa395", "name": "Short"},
                      {"uuid": "b92ef010-5e4c-4fd0-99d6-41b6456272cd", "name": "Fantasy"},
                      {"uuid": "c020dab2-e9bd-4758-95ca-dbe363462173", "name": "War"},
                      {"uuid": "ca124c76-9760-4406-bfa0-409b1e38d200", "name": "Biography"},
                      {"uuid": "ca88141b-a6b4-450d-bbc3-efa940e4953f", "name": "Mystery"},
                      {"uuid": "e508c1c8-24c0-4136-80b4-340c4befb190", "name": "Reality-TV"},
                      {"uuid": "eb7212a7-dd10-4552-bf7b-7a505a8c0b95", "name": "History"},
                      {"uuid": "f24fd632-b1a5-4273-a835-0119bd12f829", "name": "News"},
                      {"uuid": "f39d7b6d-aef2-40b1-aaf0-cf05e7048011", "name": "Horror"},
                      {"uuid": "fb58fd7f-7afd-447f-b833-e51e45e2a778", "name": "Game-Show"}], 200, 26,
          'Query for all genres'),
         ('UUID', {'UUID': '120a21cf-9097-479e-1111-13dd7198c1dd'}, {'detail': 'genre not found'}, 404, 1,
          'Right UUID without genre'),
         ('UUID', {'UUID': '111111'},
          {"detail": [{"loc": ["path", "genre_id"], "msg": "value is not a valid uuid", "type": "type_error.uuid"}]},
          422, 1, 'Wrong UUID')]

SERVICE_URL = 'http://127.0.0.1:80'


@dataclass
class HTTPResponse:
    body: dict
    headers: CIMultiDictProxy[str]
    status: int


@pytest.fixture
async def make_get_request(http_session):
    async def inner(method: str, params: dict = None) -> HTTPResponse:
        def parametrs(param: dict) -> str:
            res = ''
            for k, v in param.items():
                res = res + k + '=' + str(v) + '&'
            return res[:-1]

        if method == 'search?':
            url = SERVICE_URL + '/api/v1/genre/' + method + parametrs(params)
        if method == 'All':
            url = SERVICE_URL + '/api/v1/genre/'
        if method == 'UUID':
            url = SERVICE_URL + '/api/v1/genre/' + params['UUID']
        async with http_session.get(url) as response:
            return HTTPResponse(
                body=await response.json(),
                headers=response.headers,
                status=response.status,
            )

    return inner


tasks_ids = [a[5] for a in tasks]


@pytest.fixture(params=tasks, ids=tasks_ids)
def param_test_idfn(request):
    return request.param


@pytest.mark.asyncio
async def test_search_detailed(param_test_idfn, make_get_request):
    (method, params, body, status, ln, info) = param_test_idfn
    # Запрос
    response = await make_get_request(method, params)
    # Проверка результата
    assert response.status == status
    assert len(response.body) == ln
    assert response.body == body


@pytest.mark.asyncio
async def test_redis(make_get_request, redis_session):
    incorrect_data = "{\"uuid\":\"0b105f87-e0a5-45dc-8ce7-f8632088f390\",\"name\":\"Unknown genre\"}"
    redis_session.set('0b105f87-e0a5-45dc-8ce7-f8632088f390', incorrect_data)
    response = await make_get_request('UUID', {'UUID': '0b105f87-e0a5-45dc-8ce7-f8632088f390'})
    assert response.body == {'uuid': '0b105f87-e0a5-45dc-8ce7-f8632088f390', 'name': 'Unknown genre'}
    redis_session.delete('0b105f87-e0a5-45dc-8ce7-f8632088f390')
