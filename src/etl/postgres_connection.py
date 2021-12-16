import psycopg2
from psycopg2.extras import DictCursor

from backoff import backoff
from config import DSNSettings


class PostgresConnection:
    def __init__(self, dsn: DSNSettings):
        self.dsn = dsn

    @backoff()
    def fetch(self, query: str, args: tuple) -> list[tuple]:
        with psycopg2.connect(
            **self.dsn.dict(), cursor_factory=DictCursor
        ) as connection:
            with connection.cursor() as cursor:
                query = cursor.mogrify(query, args).decode()
                cursor.execute(query)
                res = cursor.fetchall()

        connection.close()
        return res
