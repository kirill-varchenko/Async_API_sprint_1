from pydantic import BaseModel


class DSNSettings(BaseModel):
    dbname: str
    user: str
    host: str
    port: int
    password: str = None


class ESSettings(BaseModel):
    host: str
    limit: int


class ProducerSettings(BaseModel):
    name: str
    state_file_path: str
    state_field: str
    limit: int
    sql: str


class EnricherSettings(BaseModel):
    name: str
    use: str
    sql: str


class MergerSettings(BaseModel):
    name: str
    use: list[str]
    sql: str


class LoaderSettings(BaseModel):
    name: str
    use: str
    index: str


class Config(BaseModel):
    dsn: DSNSettings
    es: ESSettings
    producers: list[ProducerSettings]
    enrichers: list[EnricherSettings]
    mergers: list[MergerSettings]
    loaders: list[LoaderSettings]
