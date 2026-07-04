import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.model.base_model import User
from app.schemas import (
    AuthTokenResponse,
    PhoneLoginRequest,
    RegisterWithCodeRequest,
    SendEmailCodeRequest,
    SendPhoneCodeRequest,
    UserCreate,
)
from app.service.verification_service import (
    send_email_verification_code,
    send_phone_verification_code,
    verify_email_code,
    verify_phone_code,
)
from app.users import get_jwt_strategy, get_user_manager

router = APIRouter(tags=["auth-ext"])

router = APIRouter(tags=["auth-ext"])


def phone_placeholder_email(phone: str) -> str:
    return f"phone{phone}@example.com"


@router.post("/send-email-code")
async def send_email_code(body: SendEmailCodeRequest, request: Request):
    await send_email_verification_code(body.email, body.scene, request)
    return {"message": "验证码已发送"}


@router.post("/send-phone-code")
async def send_phone_code(body: SendPhoneCodeRequest, request: Request):
    await send_phone_verification_code(body.phone, request)
    return {"message": "验证码已发送"}


@router.post("/register-with-code", response_model=AuthTokenResponse)
async def register_with_code(
    body: RegisterWithCodeRequest,
    user_manager=Depends(get_user_manager),
):
    await verify_email_code(body.email, "register", body.code)

    existing = await user_manager.user_db.get_by_email(body.email)
    if existing is not None:
        raise HTTPException(status_code=400, detail="邮箱已被注册")

    user_create = UserCreate(email=body.email, password=body.password)
    user = await user_manager.create(user_create)
    access_token = await get_jwt_strategy().write_token(user)
    return AuthTokenResponse(access_token=access_token)


@router.post("/login/phone", response_model=AuthTokenResponse)
async def login_with_phone(
    body: PhoneLoginRequest,
    db: AsyncSession = Depends(get_async_session),
    user_manager=Depends(get_user_manager),
):
    await verify_phone_code(body.phone, body.code)

    result = await db.execute(select(User).where(User.phone == body.phone))
    user = result.scalar_one_or_none()

    if user is None:
        email = phone_placeholder_email(body.phone)
        existing_email = await user_manager.user_db.get_by_email(email)
        if existing_email is not None:
            user = existing_email
            user.phone = body.phone
            await db.commit()
            await db.refresh(user)
        else:
            password = secrets.token_urlsafe(16) + "A1!"
            user_create = UserCreate(email=email, password=password)
            user = await user_manager.create(user_create, safe=True)
            user.phone = body.phone
            user.is_verified = True
            await db.commit()
            await db.refresh(user)

    if not user.is_active:
        raise HTTPException(status_code=400, detail="账号已被禁用")

    access_token = await get_jwt_strategy().write_token(user)
    return AuthTokenResponse(access_token=access_token)
