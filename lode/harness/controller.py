"""Central execution controller: validate -> route -> execute -> assess -> audit."""
from __future__ import annotations
import time, uuid
from .schemas import validate_task_inputs
from .safety import assess_output
from .audit import make_audit_record
from .orchestrator import TaskOrchestrator

class HarnessExecutionError(RuntimeError):
    def __init__(self, message, record=None):
        super().__init__(message); self.record = record or {}

class HarnessController:
    def __init__(self, router, audit_sink=None, orchestrator=None):
        self.router = router
        self.audit_sink = audit_sink
        self.orchestrator = orchestrator or TaskOrchestrator()

    def execute(self, *, task: str, tool: str, inputs: dict, context: dict | None = None, **tool_kwargs):
        execution_id = str(uuid.uuid4())
        started = time.perf_counter()
        try:
            routed_tool = self.orchestrator.route(task)
        except ValueError as exc:
            routed_tool = None
            route_error = str(exc)
        else:
            route_error = None
        if route_error:
            errors = [route_error]
        elif tool != routed_tool:
            errors = [f"Task {task} is routed to {routed_tool}; requested tool {tool} is not permitted"]
        else:
            errors = validate_task_inputs(task, inputs or {})
        if errors:
            record = make_audit_record(task=task, status="REJECTED", inputs=inputs,
                                       error="; ".join(errors), elapsed_ms=(time.perf_counter()-started)*1000,
                                       execution_id=execution_id)
            if self.audit_sink: self.audit_sink(record)
            raise HarnessExecutionError("Input validation failed: " + "; ".join(errors), record)
        try:
            result = self.router.call(tool, **tool_kwargs)
            safety = assess_output(task, result)
            if isinstance(result, dict):
                result = dict(result)
                result["harness"] = {"execution_id": execution_id, "task": task,
                                    "route": routed_tool,
                                    "context_summary": {"project_name": (context or {}).get("project_name", ""),
                                                        "verified_observation_count": len((context or {}).get("verified_observations", [])),
                                                        "retrieved_source_count": len((context or {}).get("retrieved_sources", []))},
                                    **safety}
            record = make_audit_record(task=task, status="COMPLETED", inputs=inputs,
                                       elapsed_ms=(time.perf_counter()-started)*1000, execution_id=execution_id)
            if self.audit_sink: self.audit_sink(record)
            return result
        except Exception as exc:
            record = make_audit_record(task=task, status="FAILED", inputs=inputs, error=exc,
                                       elapsed_ms=(time.perf_counter()-started)*1000, execution_id=execution_id)
            if self.audit_sink: self.audit_sink(record)
            if isinstance(exc, HarnessExecutionError): raise
            raise HarnessExecutionError(f"Harness tool execution failed: {type(exc).__name__}: {exc}", record) from exc
