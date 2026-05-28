from dataclasses import dataclass


@dataclass
class PresignUploadResult:
    upload_url: str
    headers: dict[str, str]
    object_key: str
    expires_in: int


@dataclass
class PresignDownloadResult:
    download_url: str
    expires_in: int


class ProviderError(Exception):
    pass
