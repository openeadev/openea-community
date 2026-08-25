from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "OpenEA Community"
    app_version: str = "1.5.2"
    page_title: str = "OpenEA Community"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://openea:openea@localhost:5432/openea"
    secret_key: str = Field(default="development-only-change-me", min_length=16)
    base_url: str = "http://localhost:8000"
    trusted_proxy_count: int = Field(default=0, ge=0)
    session_max_age_seconds: int = Field(default=28800, ge=300)

    @property
    def secure_cookies(self) -> bool:
        return self.base_url.lower().startswith("https://")

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
