from datetime import date
from typing import Optional
from uuid import UUID

from models import BaseModel


class Person(BaseModel):
    uuid: UUID
    full_name: str
    role: Optional[str] = None
    film_ids: Optional[list[UUID]] = None
