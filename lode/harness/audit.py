"""Small in-memory audit records; no secrets or raw drawing bytes are stored."""
from __future__ import annotations
from datetime import datetime, timezone
import json

SENSITIVE_KEYS = {"api_key", "groq_api_key", "image_bytes", "authorization", "token", "password"}

def _safe(value, key=""):
    if key.lower() in SENSITIVE_KEYS: return "[REDACTED]"
    if isinstance(value, dict): return {str(k): _safe(v, str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [_safe(v) for v in value[:50]]
    if isinstance(value, (str, int, float, bool)) or value is None:
        if isinstance(value, str): return value[:300]
        return value
    return str(type(value).__name__)

def make_audit_record(*, task, status, inputs=None, error=None, elapsed_ms=None, execution_id=None):
    return {"execution_id": execution_id, "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "task": task, "status": status, "elapsed_ms": round(float(elapsed_ms), 3) if elapsed_ms is not None else None,
            "inputs": _safe(inputs or {}), "error": str(error)[:500] if error else None}

def export_audit_json(records):
    return json.dumps(list(records or []), indent=2, ensure_ascii=False, default=str)
