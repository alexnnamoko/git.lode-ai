"""Small, explicit validation contracts for supported Atlas.ai tasks."""
from __future__ import annotations
import math

TASK_REQUIRED = {
    "beam_statics": ("span_m",),
    "frame_analysis": ("nodes", "members", "supports", "loads"),
    "drawing_vision": ("image_bytes", "mime_type", "prompt"),
    "engineering_adviser": ("query",),
    "beam_design": ("span_m", "width_mm", "overall_depth_mm"),
    "slab_design": ("span_m", "thickness_mm"),
    "column_design": ("width_mm", "depth_mm", "axial_load_kn"),
}


def validate_task_inputs(task: str, inputs: dict) -> list[str]:
    if task not in TASK_REQUIRED:
        return [f"Unsupported task type: {task}"]
    errors = [f"Missing required input: {key}" for key in TASK_REQUIRED[task] if key not in inputs or inputs[key] is None]
    if errors:
        return errors
    for key, value in inputs.items():
        if isinstance(value, bool) or value is None:
            continue
        if isinstance(value, (int, float)) and not math.isfinite(float(value)):
            errors.append(f"{key} must be a finite number")
    if task in {"beam_statics", "beam_design", "slab_design", "column_design"}:
        positive = {
            "beam_statics": ("span_m",),
            "beam_design": ("span_m", "width_mm", "overall_depth_mm"),
            "slab_design": ("span_m", "thickness_mm"),
            "column_design": ("width_mm", "depth_mm"),
        }[task]
        for key in positive:
            try:
                if float(inputs[key]) <= 0: errors.append(f"{key} must be greater than zero")
            except (TypeError, ValueError):
                errors.append(f"{key} must be numeric")
    if task == "beam_statics":
        if float(inputs.get("udl_kn_m", 0)) < 0: errors.append("udl_kn_m cannot be negative")
        span = float(inputs["span_m"])
        for i, load in enumerate(inputs.get("point_loads") or []):
            try:
                x, p = float(load["x_m"]), float(load["load_kn"])
                if not (0 <= x <= span): errors.append(f"Point load {i+1} must lie within the beam span")
                if p < 0: errors.append(f"Point load {i+1} cannot be negative")
            except (KeyError, TypeError, ValueError):
                errors.append(f"Point load {i+1} has an invalid structure")
    if task == "frame_analysis":
        if not isinstance(inputs["nodes"], list) or not inputs["nodes"]: errors.append("Frame nodes must be a non-empty list")
        if not isinstance(inputs["members"], list) or not inputs["members"]: errors.append("Frame members must be a non-empty list")
        if not isinstance(inputs["supports"], dict): errors.append("Frame supports must be a mapping")
        if not isinstance(inputs["loads"], dict): errors.append("Frame loads must be a mapping")
    if task == "drawing_vision":
        if not isinstance(inputs["image_bytes"], (bytes, bytearray)) or not inputs["image_bytes"]: errors.append("Drawing image is empty or invalid")
        if not str(inputs["mime_type"]).startswith("image/"): errors.append("Drawing MIME type must identify an image")
        if not str(inputs["prompt"]).strip(): errors.append("Drawing task prompt cannot be empty")
    if task == "engineering_adviser" and not str(inputs["query"]).strip(): errors.append("Engineering question cannot be empty")
    return errors
