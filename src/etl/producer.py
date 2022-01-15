from typing import Generator

from config import ProducerSettings
from postgres_connection import PostgresConnection
from state import JsonFileStorage, State


class Producer:
    def __init__(self, settings: ProducerSettings, db: PostgresConnection):
        self.settings = settings
        self.db = db
        self.state_manager = State(JsonFileStorage(self.settings.state_file_path))
        self.state = self.state_manager.get_state(self.settings.state_field)

    def produce(self) -> Generator[list[str], None, None]:
        while True:
            query = self.settings.sql
            args = (self.state, self.settings.limit)
            if not self.state:
                query = "\n".join(
                    line for line in query.split("\n") if not line.startswith("WHERE")
                )
                args = (self.settings.limit,)

            data = self.db.fetch(query, args)

            if not data:
                break

            # Сохраняется последнее полученное значение столбца соотв.
            # состоянию продьюсера
            self.state = data[-1][self.settings.state_field]

            ids = [item["id"] for item in data]

            yield ids

    def save_state(self):
        self.state_manager.set_state(self.settings.state_field, self.state)
