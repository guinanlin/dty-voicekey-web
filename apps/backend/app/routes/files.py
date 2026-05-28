from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.database import User
from app.integrations.storage_gateway_client import StorageGatewayError
from app.schemas import FileDownloadResponse, FileUploadResponse
from app.service.file_service import FileService, get_file_service
from app.users import current_active_user

router = APIRouter(tags=["files"])


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    user: User = Depends(current_active_user),
    file_service: FileService = Depends(get_file_service),
) -> FileUploadResponse:
    try:
        result = await file_service.upload_file(
            file=file,
            user_id=str(user.id),
        )
        return FileUploadResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except StorageGatewayError as exc:
        status = exc.status_code or 502
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.get("/{file_id}/download", response_model=FileDownloadResponse)
async def get_file_download_url(
    file_id: UUID,
    user: User = Depends(current_active_user),
    file_service: FileService = Depends(get_file_service),
) -> FileDownloadResponse:
    del user  # auth gate only; gateway enforces tenant scope
    try:
        result = await file_service.get_download_url(str(file_id))
        return FileDownloadResponse(**result)
    except StorageGatewayError as exc:
        status = exc.status_code or 502
        raise HTTPException(status_code=status, detail=str(exc)) from exc
