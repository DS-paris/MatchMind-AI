"""UI integration tests. Encoders/LLM responses here are explicit test doubles."""
from io import BytesIO
from pathlib import Path
import json
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"
PAGES = ["Overview", "Candidate Matching", "Semantic Search", "AI Assistant", "Candidate Intelligence", "Data & Evaluation"]


@pytest.fixture(autouse=True)
def local_test_access(monkeypatch, tmp_path):
    # Existing mocked provider tests exercise local mode. Public gating has its
    # own explicit tests in test_deployment.py; no paid provider is contacted.
    import deployment
    monkeypatch.setenv("MATCHMIND_PUBLIC", "false")
    monkeypatch.setattr(deployment, "AGENT_BUDGET", deployment.AgentBudget(tmp_path / "budget.db", cooldown=0))


def button(app, name):
    return next(b for b in app.button if b.label == name)


def build_workspace(monkeypatch, candidate_index, api_key=""):
    import matcher
    monkeypatch.setenv("OPENAI_API_KEY", api_key)
    calls = []
    def constructor(resumes):
        calls.append(resumes)
        return candidate_index
    monkeypatch.setattr(matcher, "CandidateIndex", constructor)
    app = AppTest.from_file(APP, default_timeout=30).run()
    app.checkbox[0].check().run()
    button(app, "Build candidate index").click().run()
    assert not app.exception
    return app, calls


def test_all_routes_have_honest_empty_states(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    app = AppTest.from_file(APP, default_timeout=30).run()
    for i, name in enumerate(PAGES):
        app.button(key=f"nav_{i}").click().run()
        assert not app.exception, name
        assert "index" not in app.session_state
    assert button(app, "Run reviewed evaluation").disabled
    content = "\n".join(m.value for m in app.markdown)
    assert "No evaluation results" in "\n".join(c.value for c in app.caption)
    assert "94.2%" not in content
    assert "Elena Rostova" not in content


def test_navigation_preserves_index_and_evidence(monkeypatch, candidate_index):
    app, builds = build_workspace(monkeypatch, candidate_index)
    button(app, "Search candidates").click().run()
    for i in range(len(PAGES)):
        app.button(key=f"nav_{i}").click().run()
        assert not app.exception
        assert app.session_state.index is candidate_index
        assert len(builds) == 1
        assert app.session_state.results
    app.button(key="nav_4").click().run()
    assert any("Python Python Python" in text.value for text in app.text)
    button(app, "Review requirement evidence").click().run()
    assert app.session_state.gap_result["candidate"] == "alpha"
    assert not app.exception


def test_assistant_ui_passes_real_retrieval_context(monkeypatch, candidate_index):
    import agent
    requests = []
    def fake_agent(index, question, jd, api_key, model, history, retrieval_context=None):
        requests.append((index, question, retrieval_context))
        return "Test-only response [alpha, p.1]", [{"tool": "inspect_candidate", "result": {"citation": "[alpha, p.1]"}}]
    monkeypatch.setattr(agent, "ask_agent", fake_agent)
    app, _ = build_workspace(monkeypatch, candidate_index, "test-placeholder-key")
    app.checkbox[1].check().run()
    button(app, "Search candidates").click().run()
    app.button(key="nav_3").click().run()
    button(app, "Compare top two candidates").click().run()
    assert not app.exception
    assert len(requests) == 1
    assert requests[0][0] is candidate_index
    assert len(requests[0][2]["results"]) == 2
    assert app.session_state.tool_calls[0]["tool"] == "inspect_candidate"
    assert any("Test-only response" in m["content"] for m in app.session_state.messages)
    button(app, "Generate evidence-based interview questions").click().run()
    assert "Generate 6 interview questions" in requests[-1][1]


def test_assistant_error_keeps_search_available(monkeypatch, candidate_index):
    import agent
    def unavailable(*args, **kwargs):
        raise RuntimeError("test-provider-failure")
    monkeypatch.setattr(agent, "ask_agent", unavailable)
    app, _ = build_workspace(monkeypatch, candidate_index, "test-placeholder-key")
    app.checkbox[1].check().run()
    app.button(key="nav_3").click().run()
    button(app, "Generate evidence-based interview questions").click().run()
    assert not app.exception
    assert any("RuntimeError" in e.value for e in app.error)
    assert app.session_state.index is candidate_index


def test_reviewed_evaluation_uses_current_uploaded_index(monkeypatch, candidate_index):
    import streamlit as st
    original_uploader = st.file_uploader
    raw = json.dumps([{"query": "Python Python Python", "relevant_candidate_ids": ["alpha"],
        "reviewer": "unit-test-fixture", "evidence_notes": "Controlled fixture only, not a real-world benchmark."}]).encode()
    def uploader(label, *args, **kwargs):
        if label == "Reviewed judgments JSON":
            return SimpleNamespace(size=len(raw), getvalue=lambda: raw)
        return original_uploader(label, *args, **kwargs)
    monkeypatch.setattr(st, "file_uploader", uploader)
    app, _ = build_workspace(monkeypatch, candidate_index)
    app.button(key="nav_5").click().run()
    button(app, "Run reviewed evaluation").click().run()
    assert not app.exception
    assert app.session_state.evaluation["queries"] == 1
    assert app.session_state.evaluation["details"][0]["ranking"][0]["candidate_id"] == "alpha"


def test_html_helpers_escape_external_text():
    from ui_theme import label
    assert label('<script>alert("x")</script>') == '&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;'


def test_failed_rebuild_clears_stale_index(monkeypatch, candidate_index):
    import matcher
    app, _ = build_workspace(monkeypatch, candidate_index)
    def broken(resumes):
        raise RuntimeError("test-index-load-failure")
    monkeypatch.setattr(matcher, "CandidateIndex", broken)
    button(app, "Build candidate index").click().run()
    assert not app.exception
    assert "index" not in app.session_state
    assert any("RuntimeError" in e.value for e in app.error)


def test_pdf_uploader_bytes_reach_existing_parser_and_index(monkeypatch):
    import streamlit as st
    import matcher
    from conftest import TinyEncoder
    original_uploader, index_class = st.file_uploader, matcher.CandidateIndex
    samples = APP.parent / "samples"
    uploads = [SimpleNamespace(name=p.name, getvalue=lambda data=p.read_bytes(): data)
               for p in sorted(samples.glob("*.pdf"))[:2]]
    uploads.append(SimpleNamespace(name="invalid.pdf", getvalue=lambda: b"not a pdf"))
    def uploader(label, *args, **kwargs):
        if label == "Upload PDF resumes":
            return uploads
        return original_uploader(label, *args, **kwargs)
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setattr(st, "file_uploader", uploader)
    monkeypatch.setattr(matcher, "CandidateIndex", lambda resumes: index_class(resumes, TinyEncoder()))
    app = AppTest.from_file(APP, default_timeout=30).run()
    button(app, "Build candidate index").click().run()
    assert not app.exception
    assert len(app.session_state.index.resumes) == 2
    assert any("invalid.pdf" in error.value for error in app.error)
    app.text_input[0].set_value("Python").run()
    button(app, "Search candidates").click().run()
    assert len(app.session_state.results) == 2
    assert all(row["citation"].endswith("p.1]") for row in app.session_state.results)
