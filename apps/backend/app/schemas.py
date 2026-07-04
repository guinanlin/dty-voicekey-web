import uuid
from datetime import datetime

from fastapi_users import schemas
from pydantic import BaseModel, Field
from uuid import UUID


class UserRead(schemas.BaseUser[uuid.UUID]):
    pass


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass


class ItemBase(BaseModel):
    name: str
    description: str | None = None
    quantity: int | None = None


class ItemCreate(ItemBase):
    pass


class ItemRead(ItemBase):
    id: UUID
    user_id: UUID

    model_config = {"from_attributes": True}


class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    size: int
    mime_type: str
    status: str
    download_url: str


class FileDownloadResponse(BaseModel):
    file_id: str
    download_url: str
    expires_in: int


class SendEmailCodeRequest(BaseModel):
    email: str
    scene: str = "register"


class SendPhoneCodeRequest(BaseModel):
    phone: str


class RegisterWithCodeRequest(BaseModel):
    email: str
    password: str
    code: str


class PhoneLoginRequest(BaseModel):
    phone: str
    code: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SmsUploadRequest(BaseModel):
    phone: str
    content: str
    received_at: str | None = None


class SmsBatchUploadRequest(BaseModel):
    messages: list[SmsUploadRequest]


class SmsStarRequest(BaseModel):
    starred: bool


class SmsBatchStarRequest(BaseModel):
    ids: list[UUID]
    starred: bool


class SmsBatchDeleteRequest(BaseModel):
    ids: list[UUID]


class SmsRead(BaseModel):
    id: UUID
    phone: str
    content: str
    received_at: datetime
    starred: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class SmsListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[SmsRead]


class SmsStatsResponse(BaseModel):
    total: int
    starred: int
    today: int
    this_week: int
    this_month: int


class SmsUploadResponse(BaseModel):
    id: UUID


class SmsBatchUploadResponse(BaseModel):
    success: int
    failed: int
    ids: list[UUID]


class SmsBatchActionResponse(BaseModel):
    updated: int | None = None
    deleted: int | None = None


class SmsForwardDevice(BaseModel):
    id: str
    model: str
    manufacturer: str
    androidSdk: int
    appVersion: str


class SmsForwardRule(BaseModel):
    id: int
    name: str | None = None
    senderFilter: str


class SmsForwardMessage(BaseModel):
    from_: str = Field(alias="from")
    body: str
    timestamp: int
    subscriptionId: int | None = None
    simSlot: int | None = None
    partCount: int = 1

    model_config = {"populate_by_name": True}


class SmsForwardMeta(BaseModel):
    receivedAt: int
    sentAt: int
    attempt: int = 1
    contentLength: int
    contentSha256: str


class SmsForwardInboundRequest(BaseModel):
    id: UUID
    event: str
    version: str
    device: SmsForwardDevice
    rule: SmsForwardRule
    message: SmsForwardMessage
    meta: SmsForwardMeta
