import base64
import json
import sys
import types

# Keep unit tests independent of network access and the optional Groq SDK installation.
if "groq" not in sys.modules:
    fake = types.ModuleType("groq")
    class _UnusedGroq:
        def __init__(self, *args, **kwargs):
            raise AssertionError("The live Groq client should be mocked in unit tests")
    fake.Groq = _UnusedGroq
    sys.modules["groq"] = fake

import pytest
from lode.ai.client import image_data_url, parse_json_response


def test_image_data_url_encodes_png_bytes():
    payload = b"fake-image-bytes"
    result = image_data_url(payload, "image/png")
    assert result.startswith("data:image/png;base64,")
    assert base64.b64decode(result.split(",", 1)[1]) == payload


def test_parse_json_response_plain_json():
    data = {"page_summary": "plan", "observations": []}
    assert parse_json_response(json.dumps(data)) == data


def test_parse_json_response_fenced_json():
    data = {"observations": [{"element_type": "beam"}]}
    assert parse_json_response("```json\n" + json.dumps(data) + "\n```") == data


def test_parse_json_response_rejects_non_json():
    with pytest.raises(ValueError):
        parse_json_response("I cannot provide JSON")


def test_text_request_uses_groq_and_retrieved_context(monkeypatch):
    from lode.ai import client as ai
    captured = {}
    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="Grounded response"))])
    class FakeGroq:
        def __init__(self, api_key):
            captured["api_key"] = api_key
            self.chat = types.SimpleNamespace(completions=FakeCompletions())
    monkeypatch.setattr(ai, "Groq", FakeGroq)
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    result = ai.ask_text("What is effective depth?", context="[QA | 3.4.4] source text", model="qwen/qwen3.8-27b")
    assert result == "Grounded response"
    assert captured["model"] == "qwen/qwen3.8-27b"
    assert "source text" in captured["messages"][1]["content"]


def test_image_request_sends_data_url_and_ocr_hint(monkeypatch):
    from lode.ai import client as ai
    captured = {}
    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content='{"page_summary":"test","observations":[]}'))])
    class FakeGroq:
        def __init__(self, api_key):
            self.chat = types.SimpleNamespace(completions=FakeCompletions())
    monkeypatch.setattr(ai, "Groq", FakeGroq)
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    result = ai.analyse_image(b"image", "image/png", "Inspect drawing", "B1 225 x 450", "qwen/qwen3.8-27b")
    assert "observations" in result
    user_content = captured["messages"][1]["content"]
    assert user_content[1]["image_url"]["url"].startswith("data:image/png;base64,")
    assert "B1 225 x 450" in captured["messages"][0]["content"]


def test_missing_groq_key_is_reported(monkeypatch):
    from lode.ai import client as ai
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GROQ_API_KEY is missing"):
        ai.ask_text("Hello")


def test_text_request_preserves_role_based_conversation_history(monkeypatch):
    from lode.ai import client as ai
    captured = {}
    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="Follow-up answer"))])
    class FakeGroq:
        def __init__(self, api_key):
            self.chat = types.SimpleNamespace(completions=FakeCompletions())
    monkeypatch.setattr(ai, "Groq", FakeGroq)
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    history = [{"role": "user", "content": "Explain effective depth."},
               {"role": "assistant", "content": "It is measured to the tension steel centroid."}]
    result = ai.ask_text("What if cover increases?", history=history, context="[QA | clause 3.4] evidence")
    assert result == "Follow-up answer"
    messages = captured["messages"]
    assert messages[1] == history[0]
    assert messages[2] == history[1]
    assert "clause 3.4" in messages[3]["content"]


def test_text_request_limits_history_to_recent_eight_messages(monkeypatch):
    from lode.ai import client as ai
    captured = {}
    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="ok"))])
    class FakeGroq:
        def __init__(self, api_key): self.chat = types.SimpleNamespace(completions=FakeCompletions())
    monkeypatch.setattr(ai, "Groq", FakeGroq)
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    history = [{"role": "user", "content": f"message {i}"} for i in range(12)]
    ai.ask_text("latest", history=history)
    assert len(captured["messages"]) == 10  # system + eight history + current user
    assert captured["messages"][1]["content"] == "message 4"


def test_text_request_separates_project_context_from_retrieved_material(monkeypatch):
    from lode.ai import client as ai
    captured = {}
    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="Context-aware answer"))])
    class FakeGroq:
        def __init__(self, api_key):
            self.chat = types.SimpleNamespace(completions=FakeCompletions())
    monkeypatch.setattr(ai, "Groq", FakeGroq)
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    ai.ask_text("What is the beam span?", context="SOURCE 1: clause 3.4.4",
                project_context="Project name supplied by user: Block A")
    content = captured["messages"][-1]["content"]
    assert "USER-PROVIDED PROJECT CONTEXT" in content
    assert "RETRIEVED ENGINEERING DATASET MATERIAL" in content
    assert "CURRENT USER QUESTION" in content
    assert "Block A" in content


def test_vision_prompt_labels_model_certainty_as_uncalibrated(monkeypatch):
    from lode.ai import client as ai
    captured = {}
    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content='{"observations":[]}'))])
    class FakeGroq:
        def __init__(self, api_key):
            self.chat = types.SimpleNamespace(completions=FakeCompletions())
    monkeypatch.setattr(ai, "Groq", FakeGroq)
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    ai.analyse_image(b"image", "image/png", "Inspect", model="test-model")
    system_text = captured["messages"][0]["content"]
    assert "model_certainty" in system_text
    assert "not calibrated confidence" in system_text
