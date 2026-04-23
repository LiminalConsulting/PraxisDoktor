from __future__ import annotations
import threading
from faster_whisper import WhisperModel

_model: WhisperModel | None = None
_lock = threading.Lock()


def get_model() -> WhisperModel:
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                _model = WhisperModel("medium", device="cpu", compute_type="int8")
    return _model


def transcribe(audio_path: str, vocab_terms: list[str]) -> str:
    model = get_model()
    prompt = ", ".join(vocab_terms) if vocab_terms else ""
    segments, _ = model.transcribe(
        audio_path,
        language="de",
        initial_prompt=prompt if prompt else None,
        beam_size=5,
    )
    return " ".join(seg.text.strip() for seg in segments)
