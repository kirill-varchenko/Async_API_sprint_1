from abc import ABC, abstractmethod
from typing import Optional, Union
from uuid import UUID

from api.v1 import models


class AbstractStorage(ABC):
    @abstractmethod
    def get_data_by_id(self, index: str, id: UUID, model):
        pass

    @abstractmethod
    def get_data_list_by_id(self, index: str, id: UUID, model, parameters: dict = None):
        pass

    @abstractmethod
    def get_data_by_query(self, index: str, query: str, model, parameters: dict = None):
        pass

    @abstractmethod
    async def get_person_films_from_elastic(self, index: str, person_id: UUID, model):
        pass

    @abstractmethod
    async def get_person_search_from_elastic(self, index: str, query: str, model, parameters: dict = None):
        pass

    @abstractmethod
    async def get_all_from_elastic(self, index: str, model):
        pass


class AbstractCache(ABC):
    @abstractmethod
    def get_data(self,  key: str, model, as_list: bool = False):
        pass

    @abstractmethod
    def put_data(self, key: str, data: Union[models.BaseModel, list[models.BaseModel]], as_list: bool = False, expire: int = 300):
        pass


class AbstractKeyCreator(ABC):
    @abstractmethod
    def get_key_from_id(self, pk: UUID):
        pass

    @abstractmethod
    def get_key_from_search(self, name_model: str, query: str, list_parameters: dict) -> str:
        pass

    @abstractmethod
    async def get_key_from_films_list(self, name_model: str, pk: UUID) -> str:
        pass
