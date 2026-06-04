"""
Application Settings

Centralizes all environment configuration using Pydantic Settings.
Supports .env file loading with type-safe access throughout the app.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DB_USER: str = "root"
    DB_PASSWORD: str = "password"
    DB_HOST: str = "localhost"
    DB_PORT: str = "3306"
    DB_NAME: str = "supply_chain_db"
    DATABASE_URL: str = ""

    # App
    APP_TITLE: str = "Supply Chain Time Cycle & Bottleneck Analyzer"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
