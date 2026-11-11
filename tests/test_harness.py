import pytest
from lode.harness import HarnessController, ToolRouter, build_execution_context
from lode.harness.schemas import validate_task_inputs
from lode.harness.controller import HarnessExecutionError
from lode.harness.audit import make_audit_record


def test_tool_router_only_calls_registered_tools():
    router = ToolRouter(); router.register("sum", lambda a, b: a + b)
    assert router.call("sum", a=2, b=3) == 5
    with pytest.raises(KeyError): router.call("shell", command="whoami")


def test_router_rejects_duplicate_registration():
    router = ToolRouter(); router.register("x", lambda: 1)
    with pytest.raises(ValueError): router.register("x", lambda: 2)


def test_beam_statics_input_contract_accepts_valid_case():
    assert validate_task_inputs("beam_statics", {"span_m": 6, "udl_kn_m": 10, "point_loads": []}) == []


def test_beam_statics_rejects_load_outside_span():
    errors = validate_task_inputs("beam_statics", {"span_m": 6, "udl_kn_m": 0, "point_loads": [{"x_m": 7, "load_kn": 10}]})
    assert any("within the beam span" in e for e in errors)


def test_frame_contract_rejects_empty_model():
    errors = validate_task_inputs("frame_analysis", {"nodes": [], "members": [], "supports": {}, "loads": {}})
    assert any("non-empty" in e for e in errors)


def test_controller_executes_tool_and_attaches_harness_status():
    router = ToolRouter(); router.register("groq_text_adviser", lambda x: {"answer": x})
    records = []; controller = HarnessController(router, records.append)
    result = controller.execute(task="engineering_adviser", tool="groq_text_adviser", inputs={"query": "Explain"}, x="ok")
    assert result["answer"] == "ok"
    assert result["harness"]["engineering_approval"] is False
    assert records[0]["status"] == "COMPLETED"


def test_controller_rejects_missing_input_and_audits_it():
    router = ToolRouter(); router.register("beam_statics_solver", lambda span_m: span_m)
    records = []; controller = HarnessController(router, records.append)
    with pytest.raises(HarnessExecutionError, match="Input validation failed"):
        controller.execute(task="beam_statics", tool="beam_statics_solver", inputs={}, span_m=6)
    assert records[0]["status"] == "REJECTED"


def test_controller_records_tool_failure():
    router = ToolRouter(); router.register("groq_text_adviser", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    records = []; controller = HarnessController(router, records.append)
    with pytest.raises(HarnessExecutionError, match="boom"):
        controller.execute(task="engineering_adviser", tool="groq_text_adviser", inputs={"query": "hello"})
    assert records[0]["status"] == "FAILED"


def test_context_manager_excludes_pending_observations():
    context = build_execution_context(task="drawing", verified_observations=[
        {"label": "B1", "status": "Verified by engineer"},
        {"label": "C1", "status": "Pending engineer verification"},
    ])
    assert [x["label"] for x in context["verified_observations"]] == ["B1"]


def test_audit_redacts_image_bytes_and_api_keys():
    record = make_audit_record(task="vision", status="COMPLETED", inputs={"image_bytes": b"secret", "api_key": "secret"})
    assert record["inputs"]["image_bytes"] == "[REDACTED]"
    assert record["inputs"]["api_key"] == "[REDACTED]"


def test_unsupported_task_is_rejected():
    assert "Unsupported task type" in validate_task_inputs("arbitrary_code", {})[0]


def test_controller_rejects_tool_not_allowed_for_task():
    router = ToolRouter(); router.register("frame_solver", lambda: {})
    controller = HarnessController(router)
    with pytest.raises(HarnessExecutionError, match="not permitted"):
        controller.execute(task="engineering_adviser", tool="frame_solver", inputs={"query": "hello"})


def test_adviser_can_pass_retrieval_context_to_tool_without_harness_context_collision():
    captured = {}
    def adviser(prompt, context, history=None, project_context=None, model=None):
        captured.update(prompt=prompt, context=context, history=history)
        return "adviser response"
    router = ToolRouter()
    router.register("groq_text_adviser", adviser)
    controller = HarnessController(router)
    result = controller.execute(
        task="engineering_adviser",
        tool="groq_text_adviser",
        inputs={"query": "Explain beam shear"},
        harness_context={"project_name": "Test project"},
        prompt="Explain beam shear",
        context="Retrieved BS 8110 references",
        history=[],
    )
    assert result == "adviser response"
    assert captured["context"] == "Retrieved BS 8110 references"
