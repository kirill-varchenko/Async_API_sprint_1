from datetime import date
from uuid import UUID
from models import BaseModel


class Person(BaseModel):
    uuid: UUID
    full_name: str
    role: str = None
    film_ids: list[UUID] = None