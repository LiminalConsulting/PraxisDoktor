"""Sync the process registry into the database on startup.
Idempotent: rerunnable, updates metadata, never deletes process_instances."""
from __future__ import annotations
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Process, ProcessRoleAccess, Role
from .processes import all_processes


async def sync_registry(db: AsyncSession) -> None:
    specs = all_processes()
    spec_ids = {s.id for s in specs}

    # upsert processes
    for spec in specs:
        existing = await db.get(Process, spec.id)
        if existing is None:
            db.add(Process(
                id=spec.id,
                display_name=spec.display_name,
                icon=spec.icon,
                surface=spec.surface,
                phase=spec.phase,
                chat_attached=spec.chat_attached,
                inputs=spec.inputs,
                outputs=spec.outputs,
                transition_types=spec.transition_types,
                sort_order=spec.sort_order,
            ))
        else:
            existing.display_name = spec.display_name
            existing.icon = spec.icon
            existing.surface = spec.surface
            existing.phase = spec.phase
            existing.chat_attached = spec.chat_attached
            existing.inputs = spec.inputs
            existing.outputs = spec.outputs
            existing.transition_types = spec.transition_types
            existing.sort_order = spec.sort_order

    await db.flush()

    # rewrite role access (full replace per spec)
    for spec in specs:
        await db.execute(delete(ProcessRoleAccess).where(ProcessRoleAccess.process_id == spec.id))
        for role_id in spec.roles:
            db.add(ProcessRoleAccess(process_id=spec.id, role_id=role_id))

    # remove stale processes (not present in registry anymore)
    res = await db.execute(select(Process.id))
    db_ids = {r[0] for r in res.all()}
    for stale in db_ids - spec_ids:
        await db.execute(delete(Process).where(Process.id == stale))

    await db.commit()
