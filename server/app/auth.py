from __future__ import annotations
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Cookie, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .db import get_db
from .models import User, UserRole, UserSession

ph = PasswordHasher()
_settings = get_settings()


def hash_password(plain: str) -> str:
    return ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        ph.verify(hashed, plain)
        return True
    except VerifyMismatchError:
        return False


async def create_session(db: AsyncSession, user_id: str) -> UserSession:
    sid = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=_settings.session_max_age_hours)
    session = UserSession(id=sid, user_id=user_id, created_at=now, expires_at=expires)
    db.add(session)
    await db.commit()
    return session


def set_session_cookie(response: Response, session_id: str) -> None:
    response.set_cookie(
        key=_settings.session_cookie_name,
        value=session_id,
        max_age=_settings.session_max_age_hours * 3600,
        httponly=True,
        samesite="lax",
        secure=_settings.environment != "development",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(_settings.session_cookie_name, path="/")


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    session_cookie: Annotated[str | None, Cookie(alias=_settings.session_cookie_name)] = None,
) -> User:
    if not session_cookie:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not authenticated")

    res = await db.execute(select(UserSession).where(UserSession.id == session_cookie))
    session = res.scalar_one_or_none()
    if not session or session.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "session invalid or expired")

    user = await db.get(User, session.user_id)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "user not found")
    return user


async def get_current_user_roles(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[str]:
    res = await db.execute(select(UserRole.role_id).where(UserRole.user_id == user.id))
    return [r[0] for r in res.all()]


def require_role(role_id: str):
    async def _checker(roles: Annotated[list[str], Depends(get_current_user_roles)]) -> None:
        if role_id not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"role '{role_id}' required")
    return _checker


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    user = await db.get(User, username)
    if not user or not verify_password(password, user.password_hash):
        return None
    return user
