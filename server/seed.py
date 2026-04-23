"""Seed roles, placeholder users, and sync the process registry.
Idempotent: safe to re-run; updates instead of duplicating."""
from __future__ import annotations
import asyncio
from sqlalchemy import select
from app.auth import hash_password
from app.db import SessionLocal
from app.models import Role, User, UserRole
from app.sync import sync_registry


ROLES = [
    ("praxisinhaber", "Praxisinhaber", "Owner-operator. Final authority on financials, personnel, clinical strategy."),
    ("arzt", "Arzt", "Practicing physician; sees clinical workflows."),
    ("mfa_empfang", "MFA Empfang", "Front desk: phone, check-in, appointment booking."),
    ("mfa_behandlung", "MFA Behandlung", "Treatment-room assistant: prep, materials, exam support."),
    ("mfa_abrechnung", "MFA Abrechnung", "Billing, Krankenkassen communication, invoices."),
    ("praxismanager", "Praxismanager", "Operations: scheduling, personnel, suppliers."),
]

USERS = [
    ("admin",           "Administrator",        "praxis123", ["praxisinhaber"]),
    ("dr_inhaber",      "Dr. Inhaber",          "praxis123", ["praxisinhaber", "arzt"]),
    ("dr_angestellt",   "Dr. Angestellt",       "praxis123", ["arzt"]),
    ("mfa_anna",        "Anna (Empfang)",       "praxis123", ["mfa_empfang"]),
    ("mfa_bea",         "Bea (Behandlung)",     "praxis123", ["mfa_behandlung"]),
    ("mfa_clara",       "Clara (Abrechnung)",   "praxis123", ["mfa_abrechnung"]),
    ("manager_dora",    "Dora (Management)",    "praxis123", ["praxismanager", "mfa_abrechnung"]),
]


async def seed() -> None:
    async with SessionLocal() as db:
        # roles
        for rid, name, desc in ROLES:
            existing = await db.get(Role, rid)
            if existing is None:
                db.add(Role(id=rid, display_name=name, description=desc))
            else:
                existing.display_name = name
                existing.description = desc
        await db.flush()

        # users
        for uid, name, password, roles in USERS:
            existing = await db.get(User, uid)
            if existing is None:
                db.add(User(id=uid, display_name=name, password_hash=hash_password(password)))
            else:
                existing.display_name = name
            await db.flush()
            # role assignments — replace
            from sqlalchemy import delete as sa_delete
            await db.execute(sa_delete(UserRole).where(UserRole.user_id == uid))
            for r in roles:
                db.add(UserRole(user_id=uid, role_id=r))

        await db.commit()

        # processes via registry
        # importing the package triggers registration
        import app.processes  # noqa: F401
        await sync_registry(db)

    print("Seeded roles, users, processes.")


if __name__ == "__main__":
    asyncio.run(seed())
