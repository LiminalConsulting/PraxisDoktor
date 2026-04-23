from __future__ import annotations
from typing import Annotated
from fastapi import APIRouter, Depends, Form, HTTPException, Response, status
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import (
    authenticate_user,
    clear_session_cookie,
    create_session,
    get_current_user,
    get_current_user_roles,
    set_session_cookie,
)
from ..config import get_settings
from ..db import get_db
from ..models import User, UserSession

router = APIRouter(prefix="/api/auth", tags=["auth"])
_settings = get_settings()


@router.post("/login")
async def login(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    user = await authenticate_user(db, username, password)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")
    session = await create_session(db, user.id)
    set_session_cookie(response, session.id)
    return {"ok": True, "user": {"id": user.id, "display_name": user.display_name}}


@router.post("/logout")
async def logout(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    # delete all sessions for this user (simplest safe choice)
    await db.execute(delete(UserSession).where(UserSession.user_id == user.id))
    await db.commit()
    clear_session_cookie(response)
    return {"ok": True}


@router.get("/me")
async def me(
    user: Annotated[User, Depends(get_current_user)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
):
    return {
        "id": user.id,
        "display_name": user.display_name,
        "roles": roles,
    }
