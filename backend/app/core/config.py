from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        env_prefix="INTELLIQR_",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "IntelliQR API"
    app_env: Literal["development", "test", "production"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = "intelliqr"
    mongodb_required_on_startup: bool = False
    mongodb_server_selection_timeout_ms: int = 2000

    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: Literal["HS256", "HS384", "HS512"] = "HS256"
    jwt_issuer: str = "intelliqr-api"
    jwt_audience: str = "intelliqr-web"
    access_token_expire_minutes: int = Field(default=15, ge=1, le=1440)
    refresh_token_expire_days: int = Field(default=7, ge=1, le=90)
    refresh_cookie_name: str = "intelliqr_refresh"
    cookie_secure: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
