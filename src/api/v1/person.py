from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from api.v1 import list_parameters
from api.v1.models import PersonDetail, FilmList
from services.person import PersonService, get_person_service

router = APIRouter()


@router.get('/search', response_model=list[PersonDetail])
async def person_search(query: str,
                        list_parameters: dict = Depends(list_parameters),
                        person_service: PersonService = Depends(get_person_service)) -> list[PersonDetail]:
    res = await person_service.get_by_search(query, list_parameters)
    if not res:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='person not found')
    return [PersonDetail(**person.dict()) for person in res]


@router.get('/{person_id}', response_model=PersonDetail)
async def person_details(person_id: UUID,
                         person_service: PersonService = Depends(get_person_service)) -> PersonDetail:
    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='person not found')

    return PersonDetail(**person.dict())


@router.get('/{person_id}/film', response_model=list[FilmList], deprecated=True)
async def person_films(person_id: UUID,
                       person_service: PersonService = Depends(get_person_service)) -> list[FilmList]:
    res = await person_service.get_films_by_person_id(person_id)
    if not res:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='films not found')
    return [FilmList(**film.dict()) for film in res]
