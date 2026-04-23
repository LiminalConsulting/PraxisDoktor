import json
from pathlib import Path
import db

VOCAB_DEFAULT_PATH = Path(__file__).parent / "vocab_default.json"


def load_default_vocab() -> list[str]:
    if VOCAB_DEFAULT_PATH.exists():
        with open(VOCAB_DEFAULT_PATH, encoding="utf-8") as f:
            return json.load(f)
    return []


def ensure_vocab_seeded():
    """Seed vocab from vocab_default.json if vocab table is empty."""
    existing = db.get_vocab()
    if not existing:
        terms = load_default_vocab()
        db.seed_vocab(terms)


def get_all() -> list[str]:
    return db.get_vocab()


def add(term: str):
    db.add_vocab_term(term.strip())


def remove(term: str):
    db.remove_vocab_term(term.strip())
