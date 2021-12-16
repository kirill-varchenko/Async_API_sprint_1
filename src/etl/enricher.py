from config import EnricherSettings
from postgres_connection import PostgresConnection


class Enricher:
    def __init__(self, settings: EnricherSettings, db: PostgresConnection):
        self.settings = settings
        self.db = db

    def enrich(self, ids: list[str]) -> list[str]:
        data = self.db.fetch(self.settings.sql, (tuple(ids),))
        new_ids = [item["id"] for item in data]
        return new_ids
