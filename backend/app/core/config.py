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
    api_version: str = "1.0.0"
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
    qr_storage_directory: Path = BASE_DIR.parent / "data" / "generated"
    bulk_storage_directory: Path = BASE_DIR.parent / "data" / "bulk"
    bulk_max_rows: int = Field(default=250, ge=1, le=1000)
    share_storage_directory: Path = BASE_DIR.parent / "data" / "shares"
    share_max_file_bytes: int = Field(default=25 * 1024 * 1024, ge=1024, le=250 * 1024 * 1024)
    redirect_base_url: str = "http://127.0.0.1:8000"
    frontend_base_url: str = "http://127.0.0.1:5173"
    vault_encryption_key: str | None = Field(default=None, min_length=32)
    vault_grant_expire_minutes: int = Field(default=5, ge=1, le=60)

    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: Literal["HS256", "HS384", "HS512"] = "HS256"
    jwt_issuer: str = "intelliqr-api"
    jwt_audience: str = "intelliqr-web"
    access_token_expire_minutes: int = Field(default=15, ge=1, le=1440)
    refresh_token_expire_days: int = Field(default=7, ge=1, le=90)
    refresh_cookie_name: str = "intelliqr_refresh"
    cookie_secure: bool = False
    admin_emails: list[str] = []
    smtp_host: Literal["127.0.0.1", "localhost"] | None = None
    smtp_port: int = Field(default=1025, ge=1, le=65535)
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_starttls: bool = False
    notification_from_email: str = "notifications@intelliqr.local"


@lru_cache
def get_settings() -> Settings:
    return Settings()
