"""Validation and normalisation for model-proposed drawing observations."""
from __future__ import annotations
import math
from typing import Any

ALLOWED_ELEMENTS = {"beam", "column", "slab", "wall", "grid", "dimension", "text", "other", "unknown"}
ALLOWED_CERTAINTY = {"high", "medium", "low", "unknown"}


def _clean_text(value: Any, fallback: str, max_length: int = 500) -> str:
    if value is None:
        return fallback
    text = " ".join(str(value).split())
    return text[:max_length] if text else fallback


def _validated_box(value: Any) -> list[float] | None:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        return None
    try:
        box = [float(part) for part in value]
    except (TypeError, ValueError):
        return None
    if not all(math.isfinite(part) and 0.0 <= part <= 1.0 for part in box):
        return None
    x1, y1, x2, y2 = box
    if x2 <= x1 or y2 <= y1:
        return None
    return box


def normalise_vision_response(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate response shape and make unverified status explicit on every item."""
    if not isinstance(payload, dict):
        raise ValueError("The vision response must be a JSON object.")
    raw_observations = payload.get("observations", [])
    if not isinstance(raw_observations, list):
        raise ValueError("The vision response 'observations' field must be a list.")

    observations = []
    warnings = []
    for index, raw in enumerate(raw_observations[:200]):
        if not isinstance(raw, dict):
            warnings.append(f"Observation {index + 1} was ignored because it was not an object.")
            continue
        element = _clean_text(raw.get("element_type", "unknown"), "unknown", 40).lower()
        if element not in ALLOWED_ELEMENTS:
            element = "unknown"
            warnings.append(f"Observation {index + 1} used an unsupported element type; it was set to unknown.")
        certainty = _clean_text(raw.get("model_certainty", raw.get("confidence", "unknown")), "unknown", 20).lower()
        if certainty not in ALLOWED_CERTAINTY:
            certainty = "unknown"
        box = _validated_box(raw.get("bbox_normalized"))
        if raw.get("bbox_normalized") is not None and box is None:
            warnings.append(f"Observation {index + 1} had an invalid proposed bounding box; the box was discarded.")
        observations.append({
            "element_type": element,
            "label": _clean_text(raw.get("label"), "UNKNOWN", 120),
            "value": _clean_text(raw.get("value"), "UNKNOWN", 160),
            "unit": _clean_text(raw.get("unit"), "UNKNOWN", 40),
            "location_description": _clean_text(raw.get("location_description"), "Not clear", 240),
            "bbox_normalized": box,
            "model_certainty": certainty,
            "evidence": _clean_text(raw.get("evidence"), "No supporting visual evidence described.", 500),
            "verification_status": "Pending engineer verification",
            "source_type": "Groq-hosted vision model proposal",
        })

    uncertain = payload.get("uncertain_or_missing", [])
    if not isinstance(uncertain, list):
        uncertain = ["The model returned an invalid uncertainty list; manual review is required."]
        warnings.append("The uncertain_or_missing field was not a list.")
    return {
        "page_summary": _clean_text(payload.get("page_summary"), "No reliable page summary supplied.", 1200),
        "observations": observations,
        "uncertain_or_missing": [_clean_text(item, "Unspecified uncertainty", 300) for item in uncertain[:100]],
        "validation_warnings": warnings,
        "safety_note": "Model proposals only. Model-reported certainty is not calibrated confidence. Bounding boxes, labels, dimensions and interpretations require engineer confirmation.",
    }


def merge_review_observations(
    existing: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    *,
    page: int,
    source_drawing: str,
) -> tuple[list[dict[str, Any]], int]:
    """Append new drawing proposals to the review register without duplicates."""
    rows = list(existing or [])
    signatures = {
        (row.get("page"), row.get("source_drawing"), row.get("element_type"), row.get("label"), row.get("value"))
        for row in rows
    }
    added = 0
    for item in candidates or []:
        candidate = {
            "page": page,
            "source_drawing": source_drawing,
            "element_type": item.get("element_type", "unknown"),
            "label": item.get("label", "UNKNOWN"),
            "value": item.get("value", "UNKNOWN"),
            "unit": item.get("unit", "UNKNOWN"),
            "location": item.get("location_description", "UNKNOWN"),
            "model_certainty": item.get("model_certainty", "unknown"),
            "evidence": item.get("evidence", ""),
            "status": "Pending engineer verification",
            "source": "Groq-hosted vision proposal",
        }
        signature = (candidate["page"], candidate["source_drawing"], candidate["element_type"],
                     candidate["label"], candidate["value"])
        if signature not in signatures:
            rows.append(candidate)
            signatures.add(signature)
            added += 1
    return rows, added
