"""Allowlisted tool registry. The model cannot execute arbitrary Python or shell commands."""
from __future__ import annotations
from typing import Callable, Any

class ToolRouter:
    def __init__(self): self._tools: dict[str, Callable[..., Any]] = {}
    def register(self, name: str, function: Callable[..., Any]) -> None:
        if not name or not callable(function): raise ValueError("A tool needs a name and callable function")
        if name in self._tools: raise ValueError(f"Tool already registered: {name}")
        self._tools[name] = function
    def available_tools(self) -> list[str]: return sorted(self._tools)
    def call(self, name: str, **kwargs):
        if name not in self._tools: raise KeyError(f"Tool is not allowlisted: {name}")
        return self._tools[name](**kwargs)
