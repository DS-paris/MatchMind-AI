"""Real-model integration check; requires a cached model or initial download."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from parser import parse_pdf
from matcher import CandidateIndex

root = Path(__file__).resolve().parents[1]
resumes = [parse_pdf(p.read_bytes(), p.name) for p in sorted((root / "samples").glob("*.pdf"))]
index = CandidateIndex(resumes)
rows = index.search("Python machine learning semantic search embeddings FAISS", 3)
assert len(rows) == 3
assert rows[0]["filename"] == "candidate_aurora.pdf", rows
assert all(-1 <= row["similarity"] <= 1 for row in rows)
for row in rows:
    print(row["filename"], round(row["similarity"], 4), row["citation"])
print("Real MiniLM + FAISS retrieval smoke test passed.")
