from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import String, ForeignKey, DateTime, JSON, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Transition(Base):
    """Append-only event log per process instance. Tier 2 of the undo/redo model.
    Feedback signals are a view over (feeds_back=True AND retracted_by IS NULL)."""
    __tablename__ = "transitions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    process_instance_id: Mapped[str] = mapped_column(
        ForeignKey("process_instances.id", ondelete="CASCADE"), index=True
    )
    actor: Mapped[str] = mapped_column(String(64))  # user_id or "system"
    type: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    feeds_back: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    retracted_by: Mapped[str | None] = mapped_column(
        ForeignKey("transitions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)


Index("ix_transitions_instance_ts", Transition.process_instance_id, Transition.timestamp)
