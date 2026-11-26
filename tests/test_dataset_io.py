"""Contract fixtures below are test data, never a production dataset."""
import hashlib
import json
from pathlib import Path
import pytest
from dataset_io import preprocess_records, write_staged, load_real_dataset, occupation_requirements
from matcher import CandidateIndex
from conftest import TinyEncoder


def record(source="real-anonymized", resume_id="source-1"):
    return {"source": source, "resume_id": resume_id, "ground_truth": {
        "basics": {"fname": "Testperson", "email": "private@example.com"},
        "skills": {"items": [{"category": "Programming", "skills": ["Python", "machine learning"]}]},
        "experience": {"items": [{"company": "Do Not Retain Ltd", "position": "Developer",
                                  "description": ["Testperson built Python APIs and semantic search.",
                                                  "Email private@example.com", "Age: 33"]}]},
        "education": {"items": [{"institution": "Private College", "area": "Computer Science", "studyType": "BS"}]}}}


def test_minimization_and_source_filtering():
    resumes, stats = preprocess_records([record(), record("synthetic"), record(resume_id="source-2")])
    assert stats["input_records"] == 3
    assert stats["excluded_non_real"] == 1
    assert stats["duplicates"] == 1
    assert stats["retained"] == 1
    text = resumes[0].text
    assert "Python" in text and "Computer Science" in text
    for private in ("Testperson", "private@example.com", "Do Not Retain", "Private College", "Age:"):
        assert private not in text
    assert "source-1" in resumes[0].provenance


def test_staged_review_and_integrity(tmp_path):
    path = write_staged([record()], folder=tmp_path)
    with pytest.raises(ValueError, match="privacy review"):
        load_real_dataset(tmp_path)
    (tmp_path / "review.sha256").write_text(hashlib.sha256(path.read_bytes()).hexdigest())
    resumes, metadata = load_real_dataset(tmp_path)
    assert len(resumes) == metadata["stats"]["retained"] == 1
    path.write_text(path.read_text() + " ")
    with pytest.raises(ValueError, match="privacy review"):
        load_real_dataset(tmp_path)


def test_missing_dataset_and_no_synthetic_fallback(tmp_path):
    with pytest.raises(ValueError, match="HTTP 401"):
        load_real_dataset(tmp_path)
    with pytest.raises(ValueError, match="No usable"):
        write_staged([record("synthetic")], folder=tmp_path)
    assert not list(tmp_path.iterdir())


def test_ingested_records_index_and_evidence():
    resumes, _ = preprocess_records([record()])
    index = CandidateIndex(resumes, TinyEncoder())
    rows = index.search("Python", 1)
    assert rows[0]["candidate_id"] == resumes[0].candidate_id
    assert "Python" in rows[0]["text"]
    assert index.index.ntotal == len(index.chunks)


def test_onet_transformation():
    from scripts.download_onet import build_occupations
    tables = {"occupation_data.csv": [{"O*NET-SOC Code": "test", "Title": "Developer", "Description": "Build software"}],
              "software_skills.csv": [{"O*NET-SOC Code": "test", "Workplace Example": "Python"}] * 2,
              "task_statements.csv": [{"O*NET-SOC Code": "test", "Task": "Test programs"}]}
    rows = build_occupations(tables)
    assert rows[0]["skills"] == ["Python"]
    assert occupation_requirements(rows[0]) == "Developer\nBuild software\nPython\nTest programs"


def test_installed_onet_manifest():
    from dataset_io import load_occupations
    data = load_occupations()
    if data is None:
        pytest.skip("Official O*NET files not installed")
    assert data["license"] == "CC BY 4.0"
    assert len(data["occupations"]) == data["sources"][0]["rows"]
    assert len({o["code"] for o in data["occupations"]}) == len(data["occupations"])
    assert all(s["url"].startswith("https://www.onetcenter.org/") and len(s["sha256"]) == 64
               for s in data["sources"])
    assert any("Python" in o["skills"] for o in data["occupations"])


def test_unapproved_revision_rejected(tmp_path):
    path = write_staged([record()], revision="unverified", folder=tmp_path)
    (tmp_path / "review.sha256").write_text(hashlib.sha256(path.read_bytes()).hexdigest())
    with pytest.raises(ValueError, match="provenance"):
        load_real_dataset(tmp_path)
