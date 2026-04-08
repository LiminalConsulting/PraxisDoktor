import sqlite3
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "praxisdoktor.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id          TEXT PRIMARY KEY,
                created_at  TEXT NOT NULL,
                patient_ref TEXT,
                audio_path  TEXT,
                transcript  TEXT,
                ocr_text    TEXT,
                extracted   TEXT,
                status      TEXT DEFAULT 'processing',
                done_at     TEXT
            );

            CREATE TABLE IF NOT EXISTS vocab (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                term  TEXT NOT NULL UNIQUE
            );
        """)


# --- Sessions ---

def create_session(patient_ref: str) -> dict:
    sid = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO sessions (id, created_at, patient_ref, status) VALUES (?, ?, ?, 'processing')",
            (sid, created_at, patient_ref),
        )
    return get_session(sid)


def get_session(sid: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (sid,)).fetchone()
    if row is None:
        return None
    return dict(row)


def list_sessions() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM sessions ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def update_session(sid: str, **fields):
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [sid]
    with get_conn() as conn:
        conn.execute(f"UPDATE sessions SET {set_clause} WHERE id = ?", values)


def mark_done(sid: str):
    done_at = datetime.now(timezone.utc).isoformat()
    update_session(sid, status="done", done_at=done_at)


# --- Vocab ---

def get_vocab() -> list[str]:
    with get_conn() as conn:
        rows = conn.execute("SELECT term FROM vocab ORDER BY term").fetchall()
    return [r["term"] for r in rows]


def add_vocab_term(term: str):
    with get_conn() as conn:
        conn.execute("INSERT OR IGNORE INTO vocab (term) VALUES (?)", (term,))


def remove_vocab_term(term: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM vocab WHERE term = ?", (term,))


def seed_vocab(terms: list[str]):
    with get_conn() as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO vocab (term) VALUES (?)",
            [(t,) for t in terms],
        )
