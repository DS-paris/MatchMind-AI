"""Evaluate reviewed real data only; this script supplies no relevance labels."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dataset_io import load_real_dataset
from matcher import CandidateIndex


def evaluate(index, judgments, k=3):
    if not judgments or not 1 <= k <= 50:
        raise ValueError("Provide nonempty human-reviewed judgments and k in 1–50.")
    output = []
    for pair in judgments:
        if not pair.get("reviewer") or not pair.get("evidence_notes"):
            raise ValueError("Every query requires a human reviewer and evidence notes.")
        relevant = set(pair["relevant_candidate_ids"])
        if not relevant or not relevant.issubset(index.resumes):
            raise ValueError("Relevant IDs must exist in this exact candidate corpus.")
        ranked = index.search(pair["query"], k)
        hits = [i for i, r in enumerate(ranked, 1) if r["candidate_id"] in relevant]
        output.append({"query": pair["query"], "ranking": ranked,
                       "recall_at_k": len(hits) / len(relevant),
                       "reciprocal_rank_at_k": 1 / hits[0] if hits else 0})
    return {"queries": len(output), "k": k,
            "mean_recall_at_k": sum(r["recall_at_k"] for r in output) / len(output),
            "mrr_at_k": sum(r["reciprocal_rank_at_k"] for r in output) / len(output),
            "details": output}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("judgments", type=Path)
    parser.add_argument("--k", type=int, default=3)
    args = parser.parse_args()
    resumes, metadata = load_real_dataset()
    raw = args.judgments.read_bytes()
    report = evaluate(CandidateIndex(resumes), json.loads(raw), args.k)
    report["dataset_revision"] = metadata["revision"]
    report["candidate_ids"] = [r.candidate_id for r in resumes]
    report["judgments_sha256"] = hashlib.sha256(raw).hexdigest()
    report["limitations"] = "Small subjective relevance set; no hiring suitability, fairness, or generalization validation."
    folder = Path(__file__).resolve().parents[1] / "evaluation"
    folder.mkdir(exist_ok=True)
    (folder / "local_results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "details"}, indent=2))
