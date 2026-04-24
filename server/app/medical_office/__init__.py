"""
Read-only adapter to the practice's certified PVS database (Medical Office /
INDAMED, MariaDB-backed). Single source of truth for all MO reads — nothing
in the rest of the app should query MO directly.

## Schema posture (honest)

Only the **patient master table** is currently grounded — the 14 fields are
inherited from the v1 PatientIntake build (see server/app/intake/llm.py)
which derived them from MO during on-site work. They are correct.

Everything else (Fall, Befund, AbrechnungPosition, …) is **shaped from
domain knowledge, not from MO's actual table layout** until Papa runs the
extraction script (`tooling/extract-mo-schema.sh`) on the practice server.
The interfaces below are stable; only the MariaDBAdapter implementations
need to be re-mapped to whatever MO's column names actually are.

## Two implementations

1. `MockAdapter` — deterministic synthetic data for development and tests.
2. `MariaDBAdapter` — real connection to MO. Stub until schema is grounded;
   raises `SchemaNotGrounded` on every call so we never silently return
   wrong results.

The active adapter is selected by the `MEDICAL_OFFICE_ADAPTER` env var
(default: `mock`). The /api/patientenakte/* router calls into this module.

## Read-only enforcement

The base class `MedicalOfficeAdapter` exposes only `get_*` and `list_*`.
There is no `write_*`, `update_*`, or `delete_*`. The MariaDB connection
string is constructed with a user that the deployment script will create
with `GRANT SELECT ONLY` privileges on the MO database — the second line
of defense.
"""
from .schema import (
    Patient,
    Fall,
    Befund,
    AbrechnungPosition,
    CoherenceIssue,
    SchemaNotGrounded,
)
from .adapter import MedicalOfficeAdapter, get_adapter
from .mock import MockAdapter
from .mariadb import MariaDBAdapter
from .coherence import check_coherence

__all__ = [
    "Patient",
    "Fall",
    "Befund",
    "AbrechnungPosition",
    "CoherenceIssue",
    "SchemaNotGrounded",
    "MedicalOfficeAdapter",
    "MockAdapter",
    "MariaDBAdapter",
    "get_adapter",
    "check_coherence",
]
