import pytest
from scripts.evaluate_retrieval import evaluate


def test_metrics_on_controlled_test_fixture(candidate_index):
    report = evaluate(candidate_index, [{"query": "Python Python Python",
        "relevant_candidate_ids": ["alpha"], "reviewer": "unit-test-fixture",
        "evidence_notes": "Controlled fixture; not a real-world evaluation."}], k=1)
    assert report["mean_recall_at_k"] == 1
    assert report["mrr_at_k"] == 1


def test_no_fabricated_or_unreviewed_metrics(candidate_index):
    with pytest.raises(ValueError):
        evaluate(candidate_index, [])
    with pytest.raises(ValueError, match="reviewer"):
        evaluate(candidate_index, [{"query": "Python", "relevant_candidate_ids": ["alpha"]}])
    with pytest.raises(ValueError, match="exact candidate corpus"):
        evaluate(candidate_index, [{"query": "Python", "relevant_candidate_ids": ["missing"],
            "reviewer": "unit-test-fixture", "evidence_notes": "invalid ID"}])
