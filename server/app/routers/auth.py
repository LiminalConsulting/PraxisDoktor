from __future__ import annotations
from typing import Annotated
from fastapi import APIRouter, Body, Depends, Form, HTTPException, Response, status
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import (
    authenticate_user,
    clear_session_cookie,
    create_session,
    get_current_user,
    get_current_user_roles,
    hash_password,
    set_session_cookie,
    verify_password,
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


@router.post("/change-password")
async def change_password(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    body: Annotated[dict, Body()] = ...,
):
    old = body.get("old_password", "")
    new = body.get("new_password", "")
    if not new or len(new) < 6:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Neues Passwort muss mindestens 6 Zeichen haben")
    if not verify_password(old, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Altes Passwort ist falsch")
    user.password_hash = hash_password(new)
    # invalidate all other sessions, keep the current one? Simpler: invalidate all, user must re-login.
    await db.execute(delete(UserSession).where(UserSession.user_id == user.id))
    await db.commit()
    return {"ok": True}
