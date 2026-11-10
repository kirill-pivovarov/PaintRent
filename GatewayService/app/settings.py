from functools import lru_cache
from datetime import timedelta

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field, SecretStr


class Settings(BaseSettings):
    db_host: str
    db_port: str
    db_name: str
    db_user: str
    db_password: str

    secret_key: SecretStr

    refresh_token_ttl: timedelta = timedelta(days=30)
    access_token_ttl: timedelta = timedelta(minutes=15)
    access_token_algorithm: str = "HS256"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @computed_field
    @property
    def db_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


@lru_cache
def get_settings() -> Settings:
    return Settings()