import asyncio
import json
import pytest
from agents.tool_context import ToolContext
from agent import RecruitmentContext, search_candidates, inspect_candidate, analyze_skill_gaps, ask_agent
from reports import build_report


def invoke(tool, index, args):
    context = RecruitmentContext(index)
    payload = json.dumps(args)
    wrapper = ToolContext(context, tool_name=tool.name, tool_call_id="test-call", tool_arguments=payload)
    result = asyncio.run(tool.on_invoke_tool(wrapper, payload))
    return result, context.calls


def test_real_sdk_search_tool(candidate_index):
    result, calls = invoke(search_candidates, candidate_index, {"query": "Python", "top_k": 1})
    assert "alpha" in str(result)
    assert calls[0]["tool"] == "search_candidates"


def test_real_sdk_inspection(candidate_index):
    result, calls = invoke(inspect_candidate, candidate_index, {"candidate_id": "alpha"})
    assert "Python Python Python" in str(result)
    assert "[alpha, p.1]" in str(result)
    assert calls


def test_unknown_candidate(candidate_index):
    result, _ = invoke(inspect_candidate, candidate_index, {"candidate_id": "missing"})
    assert "Unknown candidate" in str(result)


def test_real_sdk_gap_tool(candidate_index):
    result, calls = invoke(analyze_skill_gaps, candidate_index,
                           {"candidate_id": "alpha", "job_description": "Python\nDocker"})
    assert "Docker" in str(result)
    assert calls[0]["result"]["resume_evidence"]


def test_no_key(candidate_index):
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        ask_agent(candidate_index, "Compare", "Python", "")


def test_report(candidate_index):
    report = build_report(candidate_index, candidate_index.search("Python"), "Python")
    assert "[alpha, p.1]" in report
    assert "alpha.pdf" in report
    assert "not hiring suitability" in report


def test_runner_wiring(candidate_index, monkeypatch):
    from types import SimpleNamespace
    import agent

    async def fake_run(assistant, payload, *, context, max_turns, run_config):
        assert {t.name for t in assistant.tools} == {"search_candidates", "inspect_candidate", "analyze_skill_gaps"}
        assert max_turns == 8
        assert run_config.tracing_disabled
        assert assistant.model_settings.max_tokens == 1200
        assert assistant.model_settings.parallel_tool_calls is False
        assert json.loads(payload)["question"] == "Find Python"
        arguments = json.dumps({"query": "Python", "top_k": 1})
        wrapper = ToolContext(context, tool_name=search_candidates.name,
                              tool_call_id="test-call", tool_arguments=arguments)
        await search_candidates.on_invoke_tool(wrapper, arguments)
        return SimpleNamespace(final_output="Evidence [alpha, p.1]")

    monkeypatch.setattr(agent.Runner, "run", fake_run)
    answer, calls = ask_agent(candidate_index, "Find Python", "Python", "test-not-a-real-key")
    assert "[alpha, p.1]" in answer
    assert calls[0]["tool"] == "search_candidates"
