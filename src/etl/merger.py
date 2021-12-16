from config import MergerSettings
from postgres_connection import PostgresConnection


class Merger:
    def __init__(self, settings: MergerSettings, db: PostgresConnection):
        self.settings = settings
        self.db = db

    def merge(self, ids: list[str]) -> list:
        data = self.db.fetch(self.settings.sql, (tuple(ids),))
        return data
