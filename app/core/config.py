from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field

class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    SECRET_KEY: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

settings = Settings()

