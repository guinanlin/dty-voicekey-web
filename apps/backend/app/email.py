from pathlib import Path
import urllib.parse

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.core.config import settings
from app.model.base_model import User


def get_email_config():
    conf = ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
        MAIL_STARTTLS=settings.MAIL_STARTTLS,
        MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
        USE_CREDENTIALS=settings.USE_CREDENTIALS,
        VALIDATE_CERTS=settings.VALIDATE_CERTS,
        TEMPLATE_FOLDER=Path(__file__).parent / settings.TEMPLATE_DIR,
    )
    return conf


async def send_reset_password_email(user: User, token: str):
    conf = get_email_config()
    email = user.email
    base_url = f"{settings.FRONTEND_URL}/password-recovery/confirm?"
    params = {"token": token}
    encoded_params = urllib.parse.urlencode(params)
    link = f"{base_url}{encoded_params}"
    message = MessageSchema(
        subject="Password recovery",
        recipients=[email],
        template_body={"username": email, "link": link},
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    await fm.send_message(message, template_name="password_reset.html")


async def send_verification_code_email(email: str, code: str, scene: str):
    conf = get_email_config()
    subject_map = {
        "register": "传声筒 - 注册验证码",
        "reset_password": "传声筒 - 密码重置验证码",
    }
    message = MessageSchema(
        subject=subject_map.get(scene, "传声筒 - 验证码"),
        recipients=[email],
        template_body={"code": code},
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    await fm.send_message(message, template_name="verification_code.html")
