from pathlib import Path

APP_SOURCE = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")


def overview_source():
    start = APP_SOURCE.index('if page=="Overview":')
    end = APP_SOURCE.index('\nelif page=="Projects":', start)
    return APP_SOURCE[start:end]


def test_raw_code_widgets_are_not_used_in_app_ui():
    assert "st.code(" not in APP_SOURCE
    assert "st.exception(" not in APP_SOURCE


def test_direct_exception_strings_are_not_rendered_to_users():
    assert 'st.error(str(e))' not in APP_SOURCE
    assert 'st.error(f"' not in APP_SOURCE


def test_developer_diagnostics_are_available_in_dedicated_area():
    assert '"developer_diagnostics":[]' in APP_SOURCE
    assert 'Application diagnostics' in APP_SOURCE
    assert 'def report_error(' in APP_SOURCE


def test_overview_does_not_expose_developer_or_environment_diagnostics():
    overview = overview_source()
    forbidden = [
        "GROQ_API_KEY", "Tesseract", "CLIP", "Developer & Evaluation",
        "developer_diagnostics", "Test Groq API connection", "APP_VERSION",
        "System status", "Build",
    ]
    for item in forbidden:
        assert item not in overview


def test_sidebar_does_not_expose_api_key_or_build_details():
    sidebar = APP_SOURCE.split("with st.sidebar:", 1)[1].split("\n\ndef heading", 1)[0]
    assert "GROQ_API_KEY" not in sidebar
    assert "Build " not in sidebar
    assert "Tesseract" not in sidebar
