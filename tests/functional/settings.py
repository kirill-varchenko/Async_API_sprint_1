from pydantic import BaseSettings, Field


class TestSettings(BaseSettings):
    es_host: str = Field('http://127.0.0.1:9200', env='ELASTIC_HOST')
    redis_host: str = Field('http://127.0.0.1:6379', env='REDIS_HOST')
    service_url: str = Field('http://127.0.0.1:8000', env='SERVICE_URL')
    use_test_data: bool = Field(False, env='USE_TEST_DATA')

    class Config:
        env_file = '.env'

test_settings = TestSettings()
