"""Deterministic task-to-tool routing; no model-generated tool names are trusted."""
from __future__ import annotations

TASK_TOOL_MAP = {
    "beam_statics": "beam_statics_solver",
    "frame_analysis": "frame_solver",
    "drawing_vision": "groq_vision",
    "engineering_adviser": "groq_text_adviser",
    "beam_design": "rc_beam_design",
    "slab_design": "rc_slab_design",
    "column_design": "rc_column_design",
}

class TaskOrchestrator:
    def route(self, task: str) -> str:
        try:
            return TASK_TOOL_MAP[task]
        except KeyError as exc:
            raise ValueError(f"No approved workflow is registered for task: {task}") from exc
