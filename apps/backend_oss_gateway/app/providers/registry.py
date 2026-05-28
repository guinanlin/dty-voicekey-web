from app.core.config import settings
from app.providers.aliyun_oss import AliyunOSSProvider
from app.providers.base import ProviderError
from app.providers.local import LocalProvider
from app.providers.protocol import StorageProvider
from app.providers.s3_compatible import S3CompatibleProvider

_local_singleton: LocalProvider | None = None


def get_local_provider() -> LocalProvider:
    global _local_singleton
    if _local_singleton is None:
        _local_singleton = LocalProvider()
    return _local_singleton


def get_provider(name: str | None = None) -> StorageProvider:
    provider_name = (name or settings.DEFAULT_PROVIDER).lower()
    if provider_name == "local":
        return get_local_provider()
    if provider_name == "s3":
        return S3CompatibleProvider()
    if provider_name == "oss":
        return AliyunOSSProvider()
    raise ProviderError(f"Unknown provider: {provider_name}")


def default_bucket(provider_name: str) -> str:
    name = provider_name.lower()
    if name == "local":
        return settings.LOCAL_BUCKET
    if name == "s3":
        return settings.S3_BUCKET
    if name == "oss":
        return settings.OSS_BUCKET
    return "default"
