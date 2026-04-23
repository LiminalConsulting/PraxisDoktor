from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import String, ForeignKey, DateTime, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Process(Base):
    """Declarative metadata about a process kind. Synced from the registry on startup."""
    __tablename__ = "processes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(128))
    icon: Mapped[str] = mapped_column(String(64), default="square")
    surface: Mapped[str] = mapped_column(String(32))  # tool | conversation | dashboard_only
    phase: Mapped[str] = mapped_column(String(32))    # decline | dashboard_only | placeholder | co_pilot | autonomous
    chat_attached: Mapped[bool] = mapped_column(default=True)
    inputs: Mapped[list[str]] = mapped_column(JSON, default=list)
    outputs: Mapped[list[str]] = mapped_column(JSON, default=list)
    transition_types: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    sort_order: Mapped[int] = mapped_column(Integer, default=100)


class ProcessRoleAccess(Base):
    __tablename__ = "process_role_access"

    process_id: Mapped[str] = mapped_column(ForeignKey("processes.id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)


class ProcessInstance(Base):
    """A specific enactment of a process. e.g. one patient intake session."""
    __tablename__ = "process_instances"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    process_id: Mapped[str] = mapped_column(ForeignKey("processes.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(256), default="")
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
    status: Mapped[str] = mapped_column(String(32), default="open")  # open | processing | ready | done | error
    current_state: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class DashboardLayout(Base):
    """Per-user ordering of dashboard cards."""
    __tablename__ = "dashboard_layouts"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    process_id: Mapped[str] = mapped_column(ForeignKey("processes.id", ondelete="CASCADE"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
