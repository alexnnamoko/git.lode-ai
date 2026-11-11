"""Post-execution guardrails for prototype outputs."""
from __future__ import annotations

PROTOTYPE_NOTICE = "Academic research prototype; output is not construction approval or professional sign-off."

def assess_output(task: str, result) -> dict:
    issues = []
    if result is None: issues.append("Tool returned no result")
    if isinstance(result, dict):
        if result.get("error"): issues.append("Tool reported an error")
        if task in {"drawing_vision", "engineering_adviser"}:
            issues.append("AI-generated interpretation or explanation requires independent review")
        if task in {"frame_analysis", "beam_statics"}:
            if "limitations" not in result and task == "frame_analysis":
                issues.append("Analysis output did not include its limitations")
    return {"status": "REVIEW REQUIRED" if issues else "COMPLETED — REVIEW REQUIRED",
            "issues": issues, "notice": PROTOTYPE_NOTICE,
            "engineering_approval": False}
