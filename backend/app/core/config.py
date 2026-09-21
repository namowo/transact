import secrets
from typing import Annotated, Any, Literal, Optional

from pydantic import (
    AnyUrl,
    BeforeValidator,
    PostgresDsn,
    computed_field,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_list(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )

    DB_HOSTNAME: str = "localhost"
    DB_PORT: int = 5432
    DB_USERNAME: str
    DB_PASSWORD: str
    DB_NAME: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+psycopg",
            username=self.DB_USERNAME,
            password=self.DB_PASSWORD,
            host=self.DB_HOSTNAME,
            port=self.DB_PORT,
            path=self.DB_NAME,
        )

    JWT_SECRET_KEY: str = secrets.token_urlsafe(32)
    VITE_JWT_LIFETIME_SECONDS: int = 43200
    ACCESS_TOKEN_COOKIE_NAME: str = "access_token"

    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 48
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 2

    WEBAUTHN_RP_NAME: str = "TransAct"
    WEBAUTHN_CHALLENGE_TTL_SECONDS: int = 300

    # FastAPI Settings
    # Schemeless host (e.g. "transact.namowo.de"); ignored when ENVIRONMENT is "local".
    HOST_URL: str = ""
    FRONTEND_DIR: str = "../frontend/dist"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    BACKEND_CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_list)] = (
        []
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def BACKEND_URL(self) -> str:
        if self.ENVIRONMENT == "local":
            return "http://localhost:8000"
        return f"https://{self.HOST_URL.rstrip('/')}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def BACKEND_API_URL(self) -> str:
        return f"{self.BACKEND_URL}{self.API_V1_STR}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def FRONTEND_URL(self) -> str:
        if self.ENVIRONMENT == "local":
            return "http://localhost:5173"
        return f"https://{self.HOST_URL.rstrip('/')}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def WEBAUTHN_RP_ID(self) -> str:
        if self.ENVIRONMENT == "local":
            return "localhost"
        return self.HOST_URL.rstrip("/")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def WEBAUTHN_ORIGIN(self) -> str:
        return self.FRONTEND_URL

    # SMTP settings. If SMTP_HOST is unset, outgoing mail is logged to the
    # console instead of being sent - convenient for local development.
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    SMTP_FROM_EMAIL: str = "no-reply@transact.local"
    SMTP_FROM_NAME: str = "TransAct Repository"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        origins = set(str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS)

        # Always add the backend origin
        host = self.BACKEND_URL.rstrip("/")
        origins.add(host)

        # Local development → add Vite dev server
        if "localhost" in host or "127.0.0.1" in host:
            origins.add("http://localhost:5173")
            origins.add(
                "http://localhost:8000"
            )  # ensure backend origin is always included

        return list(origins)

    MAIL_TEMPLATES_DIR: str = "./utils/mail/templates"


settings = Settings()  # type: ignore
