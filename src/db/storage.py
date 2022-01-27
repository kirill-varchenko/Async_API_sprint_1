from abc import ABC, abstractmethod
from typing import Optional, Union
from uuid import UUID

from api.v1 import models


class AbstractConnection(ABC):
    @abstractmethod
    def get_connection(self):
        pass


class AbstractStorageRequest(ABC):
    @abstractmethod
    def request(self, *args, **kwargs):
        pass


class AbstractStorage(ABC):
    @abstractmethod
    def get_data_by_id(self, index: str, id: UUID, model, parameters: dict = None):
        pass

    def get_data_list_by_id(self, index: str, id: UUID, model, parameters: dict = None):
        pass

    @abstractmethod
    def get_data_by_query(self, query: str, parameters: dict = None):
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
    def get_key_from_id(self, id: UUID):
        pass
