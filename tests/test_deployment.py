from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from deployment import AccessDenied, AgentBudget, authorized, public_mode


def test_public_access_fails_closed():
    assert public_mode() and not public_mode("false")
    assert not authorized("", "")
    assert not authorized("short", "short")
    assert not authorized("a" * 32, "b" * 32)
    assert authorized("a" * 32, "a" * 32)


def test_quotas_persist_and_are_global(tmp_path):
    path = tmp_path / "budget.db"
    budget = AgentBudget(path, daily=3, hourly=2, cooldown=10)
    budget.reserve("a", now=1000)
    with pytest.raises(AccessDenied, match="wait"):
        budget.reserve("a", now=1001)
    budget.reserve("a", now=1010)
    with pytest.raises(AccessDenied, match="allowance"):
        budget.reserve("a", now=1020)
    AgentBudget(path, daily=3).reserve("b", now=1020)
    with pytest.raises(AccessDenied):
        budget.reserve("new-session", now=1030)
    budget.reserve("a", now=90000)


def test_atomic_budget_and_slot(tmp_path):
    budget = AgentBudget(tmp_path / "budget.db", daily=1, cooldown=0)
    def attempt(i):
        try:
            budget.reserve(str(i), now=1000)
            return True
        except AccessDenied:
            return False
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert sum(pool.map(attempt, range(8))) == 1
    budget = AgentBudget(tmp_path / "other.db", cooldown=0)
    with pytest.raises(RuntimeError):
        with budget.request("a"):
            with pytest.raises(AccessDenied, match="busy"):
                with budget.request("b"):
                    pass
            raise RuntimeError("provider failed")
    with budget.request("b"):
        pass


def test_public_ui_locks_key_without_access_code(monkeypatch):
    from streamlit.testing.v1 import AppTest
    monkeypatch.setenv("MATCHMIND_PUBLIC", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-placeholder-key")
    monkeypatch.delenv("MATCHMIND_AGENT_ACCESS_CODE", raising=False)
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py", default_timeout=30).run()
    assert not app.exception
    assert any("Public assistant locked" in x.value for x in app.caption)


def test_release_allowlist_excludes_private_files():
    from scripts.prepare_release import release_files, ROOT, SECRET
    files = {p.relative_to(ROOT).as_posix() for p in release_files()}
    assert ".env" not in files and ".streamlit/secrets.toml" not in files
    assert "data/onet_occupations.json" in files
    assert not any(p.startswith(("data/private/", ".cache/", "archive")) for p in files)
    assert not any(p.endswith((".csv", ".parquet", ".docx", ".zip")) for p in files)
    assert SECRET.search(b"sk-proj-" + b"a" * 40)
    assert not SECRET.search(b"OPENAI_API_KEY=your-key")


def test_public_unlock_and_quota_enforced(monkeypatch, candidate_index, tmp_path):
    import agent
    import deployment
    import matcher
    from streamlit.testing.v1 import AppTest
    requests = []
    def fake_agent(*args, **kwargs):
        requests.append(True)
        return "Explicit test double", []
    monkeypatch.setenv("MATCHMIND_PUBLIC", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-placeholder-key")
    monkeypatch.setenv("MATCHMIND_AGENT_ACCESS_CODE", "a" * 32)
    monkeypatch.setattr(matcher, "CandidateIndex", lambda resumes: candidate_index)
    monkeypatch.setattr(agent, "ask_agent", fake_agent)
    monkeypatch.setattr(deployment, "AGENT_BUDGET", AgentBudget(tmp_path / "ui.db", daily=1, cooldown=0))
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py", default_timeout=30).run()
    app.checkbox[0].check().run()
    next(b for b in app.button if b.label == "Build candidate index").click().run()
    app.checkbox[1].check().run()
    app.button(key="nav_3").click().run()
    assert app.chat_input[0].disabled
    app.text_input(key="agent_access_code").set_value("wrong").run()
    assert app.chat_input[0].disabled and not requests
    app.text_input(key="agent_access_code").set_value("a" * 32).run()
    assert not app.chat_input[0].disabled
    next(b for b in app.button if b.label == "Generate evidence-based interview questions").click().run()
    assert len(requests) == 1 and not app.exception
    next(b for b in app.button if b.label == "Generate evidence-based interview questions").click().run()
    assert len(requests) == 1
    assert any("allowance" in x.value for x in app.warning)


def test_chunk_limit_before_model_loading(monkeypatch):
    import matcher
    from parser import Resume
    monkeypatch.setattr(matcher, "load_model", lambda: pytest.fail("Must reject before loading weights"))
    with pytest.raises(ValueError, match="2,000"):
        matcher.CandidateIndex([Resume("large", "large.pdf", ("Python " * 150100,))])
