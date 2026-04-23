"""Persistent background job runner.

- Jobs are rows in the `jobs` table with status queued | running | done | error.
- On startup, any stale `running` / `queued` jobs get requeued.
- Dispatcher is a single asyncio.Task that pulls queued jobs and runs them
  in a thread executor (for blocking ML calls)."""
from __future__ import annotations
import asyncio
import uuid
from typing import Any, Awaitable, Callable

from sqlalchemy import select, update

from .db import SessionLocal
from .models import Job

_HANDLERS: dict[str, Callable[[dict[str, Any]], Awaitable[None]]] = {}
_dispatcher_task: asyncio.Task | None = None
_wake_event: asyncio.Event | None = None


def register_handler(kind: str, fn: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
    _HANDLERS[kind] = fn


async def enqueue(kind: str, payload: dict[str, Any], process_instance_id: str | None = None) -> str:
    jid = uuid.uuid4().hex
    async with SessionLocal() as db:
        db.add(Job(
            id=jid,
            kind=kind,
            process_instance_id=process_instance_id,
            payload=payload,
            status="queued",
        ))
        await db.commit()
    if _wake_event:
        _wake_event.set()
    return jid


async def requeue_stale() -> int:
    """On startup, re-mark any running/queued jobs as queued with incremented attempts."""
    async with SessionLocal() as db:
        res = await db.execute(
            update(Job)
            .where(Job.status.in_(["running", "queued"]))
            .values(status="queued", attempts=Job.attempts + 1)
            .returning(Job.id)
        )
        ids = list(res.scalars().all())
        await db.commit()
        return len(ids)


async def _run_one(job: Job) -> None:
    handler = _HANDLERS.get(job.kind)
    if handler is None:
        async with SessionLocal() as db:
            j = await db.get(Job, job.id)
            if j:
                j.status = "error"
                j.error = f"no handler registered for kind={job.kind}"
                await db.commit()
        return

    async with SessionLocal() as db:
        j = await db.get(Job, job.id)
        if j:
            j.status = "running"
            await db.commit()

    try:
        await handler(job.payload)
        async with SessionLocal() as db:
            j = await db.get(Job, job.id)
            if j:
                j.status = "done"
                j.error = None
                await db.commit()
    except Exception as e:
        async with SessionLocal() as db:
            j = await db.get(Job, job.id)
            if j:
                # after 3 attempts give up; else leave queued for retry
                j.error = str(e)[:2000]
                if j.attempts >= 3:
                    j.status = "error"
                else:
                    j.status = "queued"
                    j.attempts = j.attempts + 1
                await db.commit()


async def _dispatcher_loop() -> None:
    assert _wake_event is not None
    while True:
        async with SessionLocal() as db:
            res = await db.execute(
                select(Job).where(Job.status == "queued").order_by(Job.created_at).limit(1)
            )
            job = res.scalar_one_or_none()

        if job is None:
            _wake_event.clear()
            try:
                await asyncio.wait_for(_wake_event.wait(), timeout=10.0)
            except asyncio.TimeoutError:
                pass
            continue

        await _run_one(job)


async def start() -> None:
    global _dispatcher_task, _wake_event
    if _dispatcher_task is not None:
        return
    _wake_event = asyncio.Event()
    count = await requeue_stale()
    if count:
        print(f"[jobs] requeued {count} stale job(s)")
    _dispatcher_task = asyncio.create_task(_dispatcher_loop())


async def stop() -> None:
    global _dispatcher_task
    if _dispatcher_task:
        _dispatcher_task.cancel()
        try:
            await _dispatcher_task
        except asyncio.CancelledError:
            pass
        _dispatcher_task = None
