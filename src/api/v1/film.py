from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from api.v1 import list_parameters
from api.v1.models import FilmList, FilmDetail
from services.film import FilmService, get_film_service

router = APIRouter()

# Внедряем FilmService с помощью Depends(get_film_service)
@router.get('/{film_id}', response_model=FilmDetail)
async def film_details(film_id: UUID, film_service: FilmService = Depends(get_film_service)) -> FilmDetail:
    film = await film_service.get_by_id(film_id)
    if not film:
        # Если фильм не найден, отдаём 404 статус
        # Желательно пользоваться уже определёнными HTTP-статусами, которые содержат enum
                # Такой код будет более поддерживаемым
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='film not found')

    # Перекладываем данные из models.Film в Film
    # Обратите внимание, что у модели бизнес-логики есть поле description
        # Которое отсутствует в модели ответа API.
        # Если бы использовалась общая модель для бизнес-логики и формирования ответов API
        # вы бы предоставляли клиентам данные, которые им не нужны
        # и, возможно, данные, которые опасно возвращать
    return Film(id=film.id, title=film.title)

@router.get('/', response_model=list[FilmList])
async def film_list(filter_genre: UUID = Query(None, alias='filter[genre]'),
                    list_parameters: dict = Depends(list_parameters),
                    film_service: FilmService = Depends(get_film_service)) -> list[FilmList]:
    ...

@router.get('/search', response_model=list[FilmList])
async def film_search(query: str,
                      list_parameters: dict = Depends(list_parameters),
                      film_service: FilmService = Depends(get_film_service)) -> list[FilmList]:
    ...

