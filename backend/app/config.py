from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(Path(__file__).resolve().parents[2] / ".env"), ".env"),
        extra="ignore",
    )

    app_env: Literal["development", "test", "production"] = "development"
    database_url: str = "postgresql+psycopg://fsp:fsp@localhost:5432/fsp"
    frontend_url: str = "http://localhost:3000"
    allowed_origins: list[str] = ["http://localhost:3000"]
    cookie_secure: bool = False
    session_ttl_seconds: int = Field(default=604800, gt=0)
    verification_ttl_seconds: int = Field(default=3600, gt=0)
    mail_backend: Literal["log", "smtp"] = "log"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_starttls: bool = True
    demo_password: str | None = None

    @model_validator(mode="after")
    def validate_production(self) -> "Settings":
        if self.app_env == "production":
            if not self.cookie_secure or self.mail_backend == "log":
                raise ValueError("Production requires secure cookies and SMTP delivery")
            if not self.frontend_url.startswith("https://"):
                raise ValueError("Production frontend must use HTTPS")
        if self.mail_backend == "smtp" and (not self.smtp_host or not self.smtp_from):
            raise ValueError("SMTP_HOST and SMTP_FROM are required for SMTP delivery")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
