from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from api.v1 import list_parameters
from api.v1.models import Genre
from services.genre import GenreService, get_genre_service

router = APIRouter()


@router.get('/{genre_id}', response_model=Genre)
async def genre_details(genre_id: UUID, genre_service: GenreService = Depends(get_genre_service)) -> Genre:
    ...

@router.get('/', response_model=Genre)
async def genre_list(genre_service: GenreService = Depends(get_genre_service)) -> list[Genre]:
    ...