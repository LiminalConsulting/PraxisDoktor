from __future__ import annotations
import threading
import easyocr

_reader: easyocr.Reader | None = None
_lock = threading.Lock()


def get_reader() -> easyocr.Reader:
    global _reader
    if _reader is None:
        with _lock:
            if _reader is None:
                _reader = easyocr.Reader(["de"], gpu=False)
    return _reader


def extract_text(image_path: str) -> str:
    reader = get_reader()
    results = reader.readtext(image_path, detail=0)
    return "\n".join(results)
