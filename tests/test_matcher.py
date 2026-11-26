import numpy as np
import pytest
from matcher import normalize, requirement_evidence, CandidateIndex
from conftest import TinyEncoder
from parser import Resume


def test_cosine_and_ranking(candidate_index):
    rows = candidate_index.search("Python Python Python", 50)
    assert [r["candidate_id"] for r in rows] == ["alpha", "beta"]
    assert rows[0]["similarity"] == pytest.approx(1, abs=1e-6)
    query = normalize(TinyEncoder().encode(["Python Python Python"]))[0]
    expected = float(query @ normalize(TinyEncoder().encode(["React React React"]))[0])
    assert rows[1]["similarity"] == pytest.approx(expected, abs=1e-6)
    assert len(candidate_index.search("React", 1)) == 1


@pytest.mark.parametrize("query,k", [("", 1), ("  ", 1), ("Python", 0), ("Python", 51)])
def test_invalid_search(candidate_index, query, k):
    with pytest.raises(ValueError):
        candidate_index.search(query, k)


def test_normalization():
    assert np.linalg.norm(normalize([[3, 4]])) == pytest.approx(1)
    with pytest.raises(ValueError):
        normalize([[0, 0]])


def test_dedup_and_empty():
    resume = Resume("a", "a.pdf", ("Python",))
    index = CandidateIndex([resume, resume], TinyEncoder())
    assert len(index.search("Python")) == 1
    with pytest.raises(ValueError):
        CandidateIndex([], TinyEncoder())


def test_skill_evidence(candidate_index):
    result = requirement_evidence(candidate_index.resumes["alpha"], "Python\nDocker")
    assert result["requirements"][0]["exact_phrase_evidence"]
    assert not result["requirements"][1]["exact_phrase_evidence"]
    assert result["resume_evidence"][0]["citation"] == "[alpha, p.1]"
