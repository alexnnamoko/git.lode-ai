"""Build bounded, provenance-aware context for harness executions."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any


def build_execution_context(*, task: str, project_name: str = "", project_notes: str = "",
                            verified_observations: list[dict[str, Any]] | None = None,
                            retrieved_sources: list[dict[str, Any]] | None = None,
                            max_chars: int = 6000) -> dict[str, Any]:
    verified = [x for x in (verified_observations or [])
                if str(x.get("status", "")).strip().lower() == "verified by engineer"]
    source_summaries = []
    for item in (retrieved_sources or [])[:10]:
        source_summaries.append({k: item.get(k) for k in ("type", "title", "reference", "dataset", "record_id") if k in item})
    return {
        "task": str(task),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "project_name": str(project_name or "")[:200],
        "project_notes": str(project_notes or "")[:2000],
        "verified_observations": verified[:30],
        "retrieved_sources": source_summaries,
        "context_truncated": len(str(project_notes or "")) > 2000,
        "policy": "Only engineer-verified drawing observations are accepted as confirmed project facts. AI proposals remain unverified.",
    }
