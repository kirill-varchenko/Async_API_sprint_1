import pytest

tasks= [('search?', {'query': '', 'page[number]': 834, 'page[size]':5},[{"uuid":"ffe0d805-3595-4cc2-a892-f2bedbec4ac6","full_name":"Alun Davies","role":"actor","film_ids":["7ee0af24-1b85-4406-b442-04574d41dd3b"]}], 200, 1, 'Query for full list of persons(end of list)'),
    ('search?', {'query': 'johndear'},{"detail":"person not found"}, 404,  1,'Query for empty list (404)'),
('UUID', {'UUID':'009884ca-5a33-44ba-8fba-495a0055c70d'}, {"uuid":"009884ca-5a33-44ba-8fba-495a0055c70d","full_name":"Mazzy Star","role":"actor","film_ids":["6d22c585-0fca-4653-936e-302094c2adc7"]}, 200,4, 'Query for UUID'),
('UUID/film', {'UUID':'0031feab-8f53-412a-8f53-47098a60ac73'},[{"uuid":"bfe61bd9-5dfd-41ca-80ae-8eca998bc29d","title":"Lone Star","imdb_rating":7.4}], 200, 1, 'Query for UUID + film'),
('search?', {'query': 'dion'}, [{"uuid":"d194e243-0a8c-41d1-a970-492792026f4b","full_name":"Dion Johnstone","role":"actor","film_ids":["6d647d21-0443-47f2-ab0c-c1aab661c9a1"]}], 200, 1, 'Query for name'),
('UUID', {'UUID':'31feab-8f53-412a-8f53-47098a60ac73'},{"detail":[{"loc":["path","person_id"],"msg":"value is not a valid uuid","type":"type_error.uuid"}]}, 422,1, 'Wrong UUID'),
('UUID', {'UUID':''},{"detail":"Not Found"}, 404,1, 'Empty UUID'),
('search?', {'query': 'sayles', 'page[number]': 'adasdas', 'page[size]': 10}, {"detail": [
            {"loc": ["query", "page[number]"], "msg": "value is not a valid integer", "type": "type_error.integer"}]},
         422, 1, 'Wrong page number'),
('search?', {'query': 'sayles', 'page[number]': 0, 'page[size]': 10}, {"detail":[{"loc":["query","page[number]"],"msg":"ensure this value is greater than or equal to 1","type":"value_error.number.not_ge","ctx":{"limit_value":1}}]},
         422, 1, 'Zero page number')

        ]

PERSON_PATH = '/person/'

tasks_ids=[a[5] for a in tasks]

@pytest.fixture(params=tasks, ids=tasks_ids)
def param_test_idfn(request):
    return request.param

@pytest.mark.asyncio
async def test_search_detailed(param_test_idfn, make_get_request):
    (method, params, body,status, ln, info)=param_test_idfn
    # Запрос
    if method == 'search?':
        response = await make_get_request(PERSON_PATH + method, params)
    elif method == 'UUID':
        response = await make_get_request(PERSON_PATH + params['UUID'], {})
    elif method == 'UUID/film':
        response = await make_get_request(PERSON_PATH + params['UUID'] + '/film', {})
    else:
        raise ValueError(method)

    # Проверка результата
    assert response.status == status
    assert len(response.body) == ln
    assert response.body == body

@pytest.mark.asyncio
async def test_redis(redis_client, make_get_request):
    incorrect_data= "{\"uuid\":\"0031feab-8f53-412a-8f53-47098a60ac73\",\"full_name\":\"Alex Malikov\",\"role\":\"director, writer\",\"film_ids\":[\"bfe61bd9-5dfd-41ca-80ae-8eca998bc29d\"]}"
    await redis_client.flushall()
    await redis_client.set('0031feab-8f53-412a-8f53-47098a60ac73', incorrect_data)
    response = await make_get_request(PERSON_PATH + '0031feab-8f53-412a-8f53-47098a60ac73')
    assert response.body == {"uuid":"0031feab-8f53-412a-8f53-47098a60ac73","full_name":"Alex Malikov","role":"director, writer","film_ids":["bfe61bd9-5dfd-41ca-80ae-8eca998bc29d"]}
    await redis_client.delete('0031feab-8f53-412a-8f53-47098a60ac73')
