import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from fastapi_users.db import SQLAlchemyUserDatabase

from app.core.database import async_session_maker
from app.model.base_model import User
from app.users import UserManager, get_jwt_strategy
from app.ws.web_subscriber_manager import web_subscriber_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["relay-web-ws"])


async def _authenticate_token(token: str) -> User | None:
    if not token:
        return None
    try:
        async with async_session_maker() as session:
            user_db = SQLAlchemyUserDatabase(session, User)
            manager = UserManager(user_db)
            user = await get_jwt_strategy().read_token(token, manager)
            if user is None or not user.is_active:
                return None
            return user
    except Exception:
        logger.debug("relay web ws auth failed", exc_info=True)
        return None


@router.websocket("/relay/ws")
async def relay_web_events(websocket: WebSocket, token: str = Query(...)):
    user = await _authenticate_token(token)
    if user is None:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await websocket.accept()
    await web_subscriber_manager.subscribe(user.id, websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await web_subscriber_manager.unsubscribe(user.id, websocket)
