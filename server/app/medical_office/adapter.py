"""
Abstract base class for MO adapters + factory.

The interface is intentionally small and fully read-only: no method has a
write semantic, ever. Hard guard against introducing one (we'd rather
re-derive a write path properly than let one creep in by accident).
"""
from __future__ import annotations
import os
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Optional

from .schema import Patient, Fall, Befund, AbrechnungPosition


class MedicalOfficeAdapter(ABC):
    """Read-only access to Medical Office records.
    Implementations: MockAdapter, MariaDBAdapter."""

    name: str = "abstract"
    grounded_kinds: tuple[str, ...] = ()  # which record kinds the adapter has real data for

    # ----- Patient -----
    @abstractmethod
    def get_patient(self, patient_id: str) -> Optional[Patient]: ...

    @abstractmethod
    def search_patients(self, query: str, limit: int = 20) -> list[Patient]: ...

    @abstractmethod
    def list_patients(self, limit: int = 50, offset: int = 0) -> list[Patient]: ...

    # ----- Fall -----
    @abstractmethod
    def list_faelle_for_patient(self, patient_id: str) -> list[Fall]: ...

    # ----- Befund -----
    @abstractmethod
    def list_befunde_for_patient(self, patient_id: str) -> list[Befund]: ...

    # ----- Abrechnung -----
    @abstractmethod
    def list_positions_for_fall(self, fall_id: str) -> list[AbrechnungPosition]: ...

    @abstractmethod
    def list_positions_for_quartal(self, quartal: str) -> list[AbrechnungPosition]: ...


@lru_cache
def get_adapter() -> MedicalOfficeAdapter:
    """Pick adapter by env. Default: mock. The MariaDB adapter is selected
    on the practice server once Papa wires up credentials."""
    # Imports inside function to avoid circular imports at module load
    kind = os.environ.get("MEDICAL_OFFICE_ADAPTER", "mock").lower()
    if kind == "mariadb":
        from .mariadb import MariaDBAdapter
        return MariaDBAdapter()
    from .mock import MockAdapter
    return MockAdapter()
