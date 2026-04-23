from __future__ import annotations
from typing import Annotated
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import (
    get_current_user_roles,
    hash_password,
    require_role,
)
from ..db import get_db
from ..models import Role, User, UserRole

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(require_role("praxisinhaber"))],
)


@router.get("/users")
async def list_users(db: Annotated[AsyncSession, Depends(get_db)]):
    users = (await db.execute(select(User))).scalars().all()
    role_links = (await db.execute(select(UserRole))).scalars().all()
    by_user: dict[str, list[str]] = {}
    for rl in role_links:
        by_user.setdefault(rl.user_id, []).append(rl.role_id)
    return [
        {"id": u.id, "display_name": u.display_name, "roles": sorted(by_user.get(u.id, []))}
        for u in users
    ]


@router.get("/roles")
async def list_roles(db: Annotated[AsyncSession, Depends(get_db)]):
    res = await db.execute(select(Role))
    return [{"id": r.id, "display_name": r.display_name, "description": r.description} for r in res.scalars().all()]


@router.post("/users", status_code=201)
async def create_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    payload: Annotated[dict, Body()] = ...,
):
    uid = payload.get("id", "").strip().lower()
    display_name = payload.get("display_name", "").strip() or uid
    password = payload.get("password", "")
    roles = payload.get("roles", [])
    if not uid or not password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "id and password required")
    existing = await db.get(User, uid)
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "user already exists")
    db.add(User(id=uid, display_name=display_name, password_hash=hash_password(password)))
    for r in roles:
        if await db.get(Role, r):
            db.add(UserRole(user_id=uid, role_id=r))
    await db.commit()
    return {"ok": True}


@router.put("/users/{user_id}/roles")
async def set_user_roles(
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    roles: Annotated[list[str], Body(embed=True)] = ...,
):
    if not await db.get(User, user_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")
    await db.execute(delete(UserRole).where(UserRole.user_id == user_id))
    for r in roles:
        if await db.get(Role, r):
            db.add(UserRole(user_id=user_id, role_id=r))
    await db.commit()
    return {"ok": True}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")
    await db.delete(user)
    await db.commit()
    return {"ok": True}
