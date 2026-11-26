from streamlit.testing.v1 import AppTest
from pathlib import Path
import pytest
import ast
from streamlit.runtime.scriptrunner.magic import add_magic

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def test_app_has_no_implicit_magic_output():
    tree = add_magic(APP_PATH.read_text(encoding="utf-8"), str(APP_PATH))
    implicit_writes = [node for node in ast.walk(tree)
                       if isinstance(node, ast.Call)
                       and isinstance(node.func, ast.Attribute)
                       and isinstance(node.func.value, ast.Name)
                       and node.func.value.id == "__streamlitmagic__"
                       and node.func.attr == "transparent_write"]
    assert not implicit_writes, "Use explicit Streamlit statements to avoid rendering return values."


def assert_no_rendering_leaks(app):
    assert not app.get("code")
    for kind in ("markdown", "text", "json"):
        for element in app.get(kind):
            assert "DeltaGenerator(" not in element.value
            assert 'st.success("Assistant configured")' not in element.value


@pytest.mark.parametrize("api_key", ["", "test-placeholder-key"])
def test_sidebar_status_has_no_magic_output(monkeypatch, api_key):
    monkeypatch.setenv("OPENAI_API_KEY", api_key)
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()
    assert not app.exception
    if api_key:
        assert [item.value for item in app.sidebar.success] == ["Assistant configured"]
        assert not app.sidebar.warning
    else:
        assert [item.value for item in app.sidebar.warning] == ["Search mode · no OpenAI key"]
        assert not app.sidebar.success
    assert_no_rendering_leaks(app)


def test_no_key_landing(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()
    assert not app.exception
    assert app.title[0].value == "MatchMind AI"
    assert any("no OpenAI key" in item.value for item in app.warning)


def test_demo_search_and_clear(monkeypatch, candidate_index):
    import matcher
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setattr(matcher, "CandidateIndex", lambda resumes: candidate_index)
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()
    app.checkbox[0].check().run()
    next(b for b in app.button if b.label == "Build candidate index").click().run()
    assert not app.exception
    next(b for b in app.button if b.label == "Search candidates").click().run()
    assert not app.exception
    assert len(app.dataframe) == 1
    assert_no_rendering_leaks(app)
    assert app.chat_input[0].disabled
    next(b for b in app.button if b.label == "Clear workspace").click().run()
    assert not app.exception
    assert not app.checkbox[0].value
    assert "index" not in app.session_state


def test_dataset_unavailable_has_no_synthetic_fallback(monkeypatch):
    import dataset_io
    monkeypatch.setenv("OPENAI_API_KEY", "")

    def unavailable():
        raise ValueError(dataset_io.BLOCKER)

    monkeypatch.setattr(dataset_io, "load_real_dataset", unavailable)
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()
    app.radio[0].set_value("Real-world dataset").run()
    assert not app.exception
    assert any("HTTP 401" in w.value for w in app.sidebar.warning)
    assert next(b for b in app.button if b.label == "Build candidate index").disabled
    assert "index" not in app.session_state
    assert_no_rendering_leaks(app)


def test_dataset_source_uses_existing_search(monkeypatch, candidate_index):
    import dataset_io
    import matcher
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setattr(dataset_io, "load_real_dataset", lambda: (
        list(candidate_index.resumes.values()), {"stats": {"retained": 2}}))
    monkeypatch.setattr(matcher, "CandidateIndex", lambda resumes: candidate_index)
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()
    app.radio[0].set_value("Real-world dataset").run()
    next(b for b in app.button if b.label == "Build candidate index").click().run()
    app.text_input[0].set_value("Python").run()
    next(b for b in app.button if b.label == "Search candidates").click().run()
    assert not app.exception
    assert len(app.dataframe) == 1
    app.radio[0].set_value("Uploaded resumes").run()
    assert "index" not in app.session_state


def test_onet_requirements_populate_job_description(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()
    if not app.selectbox:
        pytest.skip("Official O*NET data not installed")
    next(b for b in app.button if b.label == "Use occupational requirements").click().run()
    assert not app.exception
    assert app.text_area[0].value.strip()
    assert app.session_state["occupation_reference"].startswith("O*NET 31.0")
