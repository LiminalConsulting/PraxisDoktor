"""Single in-process pub/sub for WebSocket broadcasts.
Channels are keyed strings: "chat:{process_id}", "process:{instance_id}", etc.
For now in-process only; a Postgres LISTEN/NOTIFY bridge can be added later
when we run multi-worker."""
from __future__ import annotations
import asyncio
import json
from collections import defaultdict
from typing import Any
from datetime import datetime, timezone

from fastapi import APIRouter, Cookie, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .db import get_db
from .models import UserSession

router = APIRouter()
_settings = get_settings()

_subs: dict[str, set[asyncio.Queue]] = defaultdict(set)


def subscribe(channel: str) -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue()
    _subs[channel].add(q)
    return q


def unsubscribe(channel: str, q: asyncio.Queue) -> None:
    _subs[channel].discard(q)
    if not _subs[channel]:
        _subs.pop(channel, None)


async def broadcast(channel: str, event: dict[str, Any]) -> None:
    for q in list(_subs.get(channel, ())):
        q.put_nowait(event)


async def _ws_user_id(db: AsyncSession, cookie: str | None) -> str | None:
    if not cookie:
        return None
    s = await db.get(UserSession, cookie)
    if not s:
        return None
    if s.expires_at < datetime.now(timezone.utc):
        return None
    return s.user_id


@router.websocket("/ws")
async def ws_endpoint(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db),
):
    cookie = websocket.cookies.get(_settings.session_cookie_name)
    user_id = await _ws_user_id(db, cookie)
    if not user_id:
        await websocket.close(code=4401)
        return

    await websocket.accept()
    queues: dict[str, asyncio.Queue] = {}
    pump_tasks: list[asyncio.Task] = []

    async def pump(channel: str, q: asyncio.Queue) -> None:
        try:
            while True:
                event = await q.get()
                await websocket.send_text(json.dumps({"channel": channel, "event": event}))
        except Exception:
            return

    try:
        await websocket.send_text(json.dumps({"channel": "system", "event": {"type": "ready", "user_id": user_id}}))
        while True:
            text = await websocket.receive_text()
            try:
                msg = json.loads(text)
            except json.JSONDecodeError:
                continue
            action = msg.get("action")
            if action == "subscribe":
                ch = msg.get("channel", "")
                if ch and ch not in queues:
                    q = subscribe(ch)
                    queues[ch] = q
                    pump_tasks.append(asyncio.create_task(pump(ch, q)))
                    await websocket.send_text(json.dumps({"channel": "system", "event": {"type": "subscribed", "channel": ch}}))
            elif action == "unsubscribe":
                ch = msg.get("channel", "")
                if ch in queues:
                    unsubscribe(ch, queues.pop(ch))
                    await websocket.send_text(json.dumps({"channel": "system", "event": {"type": "unsubscribed", "channel": ch}}))
            elif action == "ping":
                await websocket.send_text(json.dumps({"channel": "system", "event": {"type": "pong"}}))
    except WebSocketDisconnect:
        pass
    finally:
        for ch, q in queues.items():
            unsubscribe(ch, q)
        for t in pump_tasks:
            t.cancel()
