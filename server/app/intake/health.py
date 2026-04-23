from __future__ import annotations
import httpx
from ..config import get_settings


def ollama_status() -> dict:
    """Check that Ollama is reachable AND has the configured model pulled."""
    s = get_settings()
    try:
        r = httpx.get(f"{s.ollama_host}/api/tags", timeout=3.0)
        r.raise_for_status()
        models = [m.get("name", "") for m in r.json().get("models", [])]
        has_model = any(m.startswith(s.ollama_model) for m in models)
        return {
            "reachable": True,
            "model_present": has_model,
            "expected_model": s.ollama_model,
            "available_models": models,
        }
    except httpx.ConnectError:
        return {"reachable": False, "error": "connection_refused", "expected_model": s.ollama_model}
    except httpx.HTTPError as e:
        return {"reachable": False, "error": str(e), "expected_model": s.ollama_model}
