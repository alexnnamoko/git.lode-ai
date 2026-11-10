from pathlib import Path

APP_SOURCE = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")


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
