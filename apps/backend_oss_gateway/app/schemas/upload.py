from pydantic import BaseModel, Field


class PresignUploadRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=512)
    size: int = Field(..., ge=1)
    mime_type: str = Field(..., min_length=1, max_length=255)
    provider: str | None = None
    visibility: str = "private"


class PresignUploadResponse(BaseModel):
    file_id: str
    upload_url: str
    headers: dict[str, str]
    object_key: str
    provider: str
    expires_in: int


class CompleteUploadRequest(BaseModel):
    file_id: str
    object_key: str
    hash: str | None = None
    size: int | None = None
    mime_type: str | None = None
    idempotency_key: str | None = None
    biz_type: str | None = None
    biz_id: str | None = None


class CompleteUploadResponse(BaseModel):
    file_id: str
    status: str
    object_key: str


class DownloadUrlResponse(BaseModel):
    file_id: str
    download_url: str
    expires_in: int


class DeleteFileResponse(BaseModel):
    file_id: str
    status: str
