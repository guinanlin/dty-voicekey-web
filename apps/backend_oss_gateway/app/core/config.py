from typing import Set

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    OPENAPI_URL: str = "/openapi.json"

    DATABASE_URL: str
    TEST_DATABASE_URL: str | None = None
    EXPIRE_ON_COMMIT: bool = False

    SERVICE_TOKENS: str = "dev-service-token-change-in-production"
    DEFAULT_PROVIDER: str = "local"

    LOCAL_STORAGE_PATH: str = "./storage"
    LOCAL_BUCKET: str = "local-dev"
    LOCAL_PUBLIC_BASE_URL: str = "http://localhost:8020"

    S3_ENDPOINT_URL: str | None = None
    S3_ACCESS_KEY: str | None = None
    S3_SECRET_KEY: str | None = None
    S3_REGION: str = "us-east-1"
    S3_BUCKET: str = "dev-bucket"

    OSS_ACCESS_KEY_ID: str | None = None
    OSS_ACCESS_KEY_SECRET: str | None = None
    OSS_ENDPOINT: str = "oss-cn-hangzhou.aliyuncs.com"
    OSS_BUCKET: str = "dev-bucket"

    PRESIGN_UPLOAD_TTL: int = 3600
    PRESIGN_DOWNLOAD_TTL: int = 3600

    CORS_ORIGINS: Set[str] = {"*"}

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def service_token_set(self) -> set[str]:
        return {t.strip() for t in self.SERVICE_TOKENS.split(",") if t.strip()}


settings = Settings()
