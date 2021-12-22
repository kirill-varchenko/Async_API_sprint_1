from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from api.v1 import list_parameters
from api.v1.models import FilmList, FilmDetail
from services.film import FilmService, get_film_service

router = APIRouter()

@router.get('/search', response_model=list[FilmList])
async def film_search(query: str,
                      list_parameters: dict = Depends(list_parameters),
                      film_service: FilmService = Depends(get_film_service)) -> list[FilmList]:
    films = await film_service.search(query, list_parameters)
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='films not found')

    return [FilmList(**film.dict()) for film in films]

# Внедряем FilmService с помощью Depends(get_film_service)
@router.get('/{film_id}', response_model=FilmDetail)
async def film_details(film_id: UUID, film_service: FilmService = Depends(get_film_service)) -> FilmDetail:
    film = await film_service.get_by_id(film_id)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='film not found')

    return FilmDetail(**film.dict())

@router.get('/', response_model=list[FilmList])
async def film_list(filter_genre: UUID = Query(None, alias='filter[genre]'),
                    list_parameters: dict = Depends(list_parameters),
                    film_service: FilmService = Depends(get_film_service)) -> list[FilmList]:
    films = await film_service.list_films(filter_genre, list_parameters)
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='films not found')

    return [FilmList(**film.dict()) for film in films]

