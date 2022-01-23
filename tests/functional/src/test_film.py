import pytest

FILMS_PATH = '/film'

### Проверка валидации параметров в film/search ###

@pytest.mark.asyncio
async def test_data_validation_search_empty(make_get_request):
    response = await make_get_request(f'{FILMS_PATH}/search', {})

    assert response.status == 422
    assert len(response.body) == 1
    assert response.body == {'detail': [{'loc': ['query', 'query'],
                                         'msg': 'field required',
                                         'type': 'value_error.missing'}]}

@pytest.mark.asyncio
async def test_data_validation_search_some(make_get_request):
    response = await make_get_request(f'{FILMS_PATH}/search', {'query': 'somequery'})

    assert response.status == 404
    assert len(response.body) == 1
    assert response.body == {'detail': 'films not found'}

@pytest.mark.asyncio
async def test_data_validation_search_film_ok(make_get_request):
    response = await make_get_request(f'{FILMS_PATH}/search', {'query': 'Star Wars'})

    assert response.status == 200
    assert len(response.body) > 0

@pytest.mark.asyncio
async def test_data_validation_search_page_size_ok(make_get_request):
    response = await make_get_request(f'{FILMS_PATH}/search', {'query': 'Star Wars',
                                                               'page[size]': 10})

    assert response.status == 200
    assert len(response.body) == 10

@pytest.mark.asyncio
async def test_data_validation_search_page_size_zero(make_get_request):
    response = await make_get_request(f'{FILMS_PATH}/search', {'query': 'Star Wars',
                                                               'page[size]': 0})

    assert response.status == 404
    assert len(response.body) == 1
    assert response.body == {'detail': 'films not found'}

@pytest.mark.asyncio
async def test_data_validation_search_page_size_negative(make_get_request):
    response = await make_get_request(f'{FILMS_PATH}/search', {'query': 'Star Wars',
                                                               'page[size]': -1})

    assert response.status == 422
    assert len(response.body) == 1


@pytest.mark.asyncio
async def test_data_validation_search_page_size_not_numeric(make_get_request):
    response = await make_get_request(f'{FILMS_PATH}/search', {'query': 'Star Wars',
                                                               'page[size]': 'a'})

    assert response.status == 422
    assert len(response.body) == 1
    assert response.body == {'detail': [{'loc': ['query', 'page[size]'],
                                         'msg': 'value is not a valid integer',
                                         'type': 'type_error.integer'}]}

@pytest.mark.asyncio
async def test_data_validation_search_page_number_ok(make_get_request):
    response = await make_get_request(f'{FILMS_PATH}/search', {'query': 'Star Wars',
                                                               'page[number]': 1})

    assert response.status == 200
    assert len(response.body) > 0

@pytest.mark.asyncio
async def test_data_validation_search_page_number_zero(make_get_request):
    response = await make_get_request(f'{FILMS_PATH}/search', {'query': 'Star Wars',
                                                               'page[number]': 0})

    assert response.status == 404
    assert len(response.body) == 1
    assert response.body == {'detail': 'films not found'}

@pytest.mark.asyncio
async def test_data_validation_search_page_number_negative(make_get_request):
    response = await make_get_request(f'{FILMS_PATH}/search', {'query': 'Star Wars',
                                                               'page[number]': -1})

    assert response.status == 422
    assert len(response.body) == 1


@pytest.mark.asyncio
async def test_data_validation_search_page_number_not_numeric(make_get_request):
    response = await make_get_request(f'{FILMS_PATH}/search', {'query': 'Star Wars',
                                                               'page[number]': 'a'})

    assert response.status == 422
    assert len(response.body) == 1
    assert response.body == {'detail': [{'loc': ['query', 'page[number]'],
                                         'msg': 'value is not a valid integer',
                                         'type': 'type_error.integer'}]}

### Проверка валидации параметров поиска фильма по айди ###
@pytest.mark.asyncio
async def test_search_for_film_invalid_id(make_get_request):
    response = await make_get_request(f'{FILMS_PATH}/test', {})

    assert response.status == 422
    assert len(response.body) == 1
    assert response.body == {'detail': [{'loc': ['path', 'film_id'],
                                         'msg': 'value is not a valid uuid',
                                         'type': 'type_error.uuid'}]}

### Проверка поиска конкретного фильма ###
@pytest.mark.asyncio
async def test_search_for_film(make_get_request):
    response = await make_get_request(f'{FILMS_PATH}/e7e6d147-cc10-406c-a7a2-5e0be2231327', {})

    assert response.status == 200
    assert response.body.get('title') == 'Shooting Star'

### Вывести все фильмы ###
@pytest.mark.asyncio
async def test_list_films(make_get_request):
    response = await make_get_request(f'{FILMS_PATH}/', {'page[size]': 50,
                                                         'page[number]': 1})

    assert response.status == 200
    assert len(response.body) == 50

### Поиск с учётом кэша в Redis ###

    # Создать индекс в Elasticsearch.
    # Заполнить данные в Elasticsearch.
    # Сбросить кеш в Redis через flushall.
    # Послать запрос в сервис.
    # Проверить полученный результат:
    #     HTTP-код — 200,
    #     вернулся один элемент,
    #     тело ответа совпадает с ожидаемым.
    # Удалить данные из индекса в Elasticsearch.
