"""Whisper vocab — loaded from a static JSON file. Dynamic vocab editor
from v1 deferred."""
from __future__ import annotations
import json
from pathlib import Path

VOCAB_DEFAULT_PATH = Path(__file__).parent / "vocab_default.json"


def load_default_vocab() -> list[str]:
    if VOCAB_DEFAULT_PATH.exists():
        with VOCAB_DEFAULT_PATH.open(encoding="utf-8") as f:
            return json.load(f)
    return []


def get_all() -> list[str]:
    return load_default_vocab()
