"""Build compact, conservative project context for Atlas.ai conversations."""
from __future__ import annotations
from typing import Any


def build_project_context(
    project_name: str = "",
    project_notes: str = "",
    verified_observations: list[dict[str, Any]] | None = None,
    max_chars: int = 5000,
) -> str:
    """Include project notes and only observations explicitly marked verified.

    Model-proposed and pending drawing observations are deliberately excluded so
    they cannot silently become accepted engineering inputs in later chat turns.
    """
    sections = []
    if project_name.strip():
        sections.append(f"Project name supplied by user: {project_name.strip()[:200]}")
    if project_notes.strip():
        sections.append(f"Project description/design basis supplied by user: {project_notes.strip()[:2500]}")
    verified = [
        item for item in (verified_observations or [])
        if str(item.get("status", "")).strip().lower() == "verified by engineer"
    ]
    if verified:
        lines = []
        for item in verified[:30]:
            lines.append(
                "- " + "; ".join([
                    f"element={item.get('element_type', 'unknown')}",
                    f"label={item.get('label', 'unknown')}",
                    f"value={item.get('value', 'unknown')}",
                    f"unit={item.get('unit', 'unknown')}",
                    f"drawing page={item.get('page', 'unknown')}",
                    f"review status={item.get('status', 'unknown')}",
                ])
            )
        sections.append("Drawing observations explicitly marked Verified by engineer:\n" + "\n".join(lines))
    if not sections:
        return ""
    return "\n\n".join(sections)[:max_chars]
