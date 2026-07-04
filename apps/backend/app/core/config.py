from typing import Set

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # OpenAPI docs
    OPENAPI_URL: str = "/openapi.json"

    # Database
    DATABASE_URL: str
    TEST_DATABASE_URL: str | None = None
    EXPIRE_ON_COMMIT: bool = False

    # User
    ACCESS_SECRET_KEY: str
    RESET_PASSWORD_SECRET_KEY: str
    VERIFICATION_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 7200

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Email
    MAIL_USERNAME: str | None = None
    MAIL_PASSWORD: str | None = None
    MAIL_FROM: str | None = None
    MAIL_SERVER: str | None = None
    MAIL_PORT: int | None = None
    MAIL_FROM_NAME: str = "FastAPI template"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True
    TEMPLATE_DIR: str = "email_templates"

    # Frontend
    FRONTEND_URL: str = "http://localhost:3600"

    # CORS
    CORS_ORIGINS: Set[str] = {"*"}

    # OSS Gateway (storage calls go through gateway, not vendor SDKs)
    OSS_GATEWAY_BASE_URL: str = "http://localhost:8610"
    OSS_GATEWAY_SERVICE_TOKEN: str = "dev-service-token-change-in-production"

    # SMS Forward Webhook (Android device inbound)
    SMS_FORWARD_REQUIRE_API_KEY: bool = True
    SMS_FORWARD_DEFAULT_USER_EMAIL: str = "admin@dty.com"
    SMS_FORWARD_DEFAULT_API_KEY: str = "dev-sms-forward-key-change-in-production"

    # Cloud Relay Hub
    RELAY_PUBLIC_WS_URL: str = "ws://localhost:8600/ws"
    RELAY_REQUIRE_WSS: bool = False
    RELAY_PAIR_TOKEN_TTL_DAYS: int = 0
    RELAY_MAX_PHONES_PER_PAIR: int = 3
    RELAY_TRANSMIT_RATE_LIMIT: int = 10

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
