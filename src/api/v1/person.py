from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from api.v1 import list_parameters
from api.v1.models import PersonList, PersonDetail, FilmList
from services.person import PersonService, get_person_service

router = APIRouter()

@router.get('/{person_id}', response_model=PersonDetail)
async def person_details(person_id: UUID,
                         person_service: PersonService = Depends(get_person_service)) -> PersonDetail:
    ...

@router.get('/{person_id}/film', response_model=list[FilmList], deprecated=True)
async def person_films(person_id: UUID,
                       person_service: PersonService = Depends(get_person_service)) -> list[FilmList]:
    ...


@router.get('/search', response_model=list[PersonList])
async def person_search(query: str,
                        list_parameters: dict = Depends(list_parameters),
                        person_service: PersonService = Depends(get_person_service)) -> list[PersonList]:
    ...
