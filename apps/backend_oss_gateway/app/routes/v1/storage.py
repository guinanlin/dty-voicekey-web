from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.providers.registry import get_local_provider
from app.schemas.common import HealthResponse
from app.schemas.upload import (
    CompleteUploadRequest,
    CompleteUploadResponse,
    DeleteFileResponse,
    DownloadUrlResponse,
    PresignUploadRequest,
    PresignUploadResponse,
)
from app.services.storage_service import StorageService

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


upload_router = APIRouter(prefix="/upload", tags=["upload"])
files_router = APIRouter(prefix="/files", tags=["files"])


def _tenant_id(request: Request) -> str:
    return getattr(request.state, "tenant_id", "default")


def _service(request: Request, session: AsyncSession = Depends(get_async_session)):
    return StorageService(session)


@upload_router.post("/presign", response_model=PresignUploadResponse)
async def presign_upload(
    body: PresignUploadRequest,
    request: Request,
    service: StorageService = Depends(_service),
) -> PresignUploadResponse:
    try:
        result = await service.presign_upload(
            tenant_id=_tenant_id(request),
            filename=body.filename,
            size=body.size,
            mime_type=body.mime_type,
            provider_name=body.provider,
            visibility=body.visibility,
        )
        return PresignUploadResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@upload_router.post("/complete", response_model=CompleteUploadResponse)
async def complete_upload(
    body: CompleteUploadRequest,
    request: Request,
    service: StorageService = Depends(_service),
) -> CompleteUploadResponse:
    try:
        result = await service.complete_upload(
            tenant_id=_tenant_id(request),
            file_id=body.file_id,
            object_key=body.object_key,
            file_hash=body.hash,
            size=body.size,
            mime_type=body.mime_type,
            idempotency_key=body.idempotency_key,
            biz_type=body.biz_type,
            biz_id=body.biz_id,
        )
        return CompleteUploadResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@upload_router.put("/local/{token}")
async def local_upload(token: str, request: Request) -> dict:
    """Dev-only local provider upload endpoint (small files)."""
    provider = get_local_provider()
    resolved = provider.resolve_upload_token(token)
    if not resolved:
        raise HTTPException(status_code=404, detail="Invalid or expired upload token")
    bucket, object_key = resolved
    data = await request.body()
    provider.save_upload(bucket, object_key, data)
    provider.consume_upload_token(token)
    return {"status": "uploaded", "object_key": object_key}


@files_router.get("/{file_id}/download", response_model=DownloadUrlResponse)
async def download_file(
    file_id: str,
    request: Request,
    service: StorageService = Depends(_service),
) -> DownloadUrlResponse:
    try:
        result = await service.get_download_url(
            tenant_id=_tenant_id(request), file_id=file_id
        )
        return DownloadUrlResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@files_router.delete("/{file_id}", response_model=DeleteFileResponse)
async def delete_file(
    file_id: str,
    request: Request,
    service: StorageService = Depends(_service),
) -> DeleteFileResponse:
    try:
        result = await service.delete_file(
            tenant_id=_tenant_id(request), file_id=file_id
        )
        return DeleteFileResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@files_router.get("/local/{bucket}/{object_key:path}")
async def serve_local_file(bucket: str, object_key: str) -> Response:
    provider = get_local_provider()
    data = provider.read_file(bucket, object_key)
    if data is None:
        raise HTTPException(status_code=404, detail="File not found")
    return Response(content=data)
