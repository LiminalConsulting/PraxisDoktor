"""Declarative process registry. Each module imports `register` and declares
a process; on app startup the registry is synced into the database tables."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProcessSpec:
    id: str
    display_name: str
    icon: str
    surface: str  # tool | conversation | dashboard_only
    phase: str    # decline | dashboard_only | placeholder | co_pilot | autonomous
    roles: list[str]
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    chat_attached: bool = True
    transition_types: dict[str, dict[str, Any]] = field(default_factory=dict)
    sort_order: int = 100


_REGISTRY: dict[str, ProcessSpec] = {}


def register(spec: ProcessSpec) -> ProcessSpec:
    if spec.id in _REGISTRY:
        raise ValueError(f"duplicate process registration: {spec.id}")
    _REGISTRY[spec.id] = spec
    return spec


def all_processes() -> list[ProcessSpec]:
    return sorted(_REGISTRY.values(), key=lambda p: (p.sort_order, p.id))


def get_process(pid: str) -> ProcessSpec | None:
    return _REGISTRY.get(pid)
