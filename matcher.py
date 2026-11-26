"""Real Sentence Transformer embeddings and normalized FAISS inner-product search."""
from functools import lru_cache
from pathlib import Path
import os
import re
from threading import Lock
import faiss
import numpy as np
from parser import Resume
from privacy import professional_text, validate_query


_MODEL_LOCK = Lock()


@lru_cache(maxsize=1)
def _load_model():
    import torch
    torch.set_num_threads(2)
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2",
        device="cpu", trust_remote_code=False,
        cache_folder=os.getenv("MATCHMIND_MODEL_CACHE", str(Path(__file__).parent / ".cache" / "models")))


def load_model():
    # Single-flight loading: concurrent sessions share exactly one model.
    with _MODEL_LOCK:
        return _load_model()


def normalize(vectors):
    array = np.ascontiguousarray(vectors, dtype=np.float32)
    if array.ndim != 2 or not np.isfinite(array).all():
        raise ValueError("Embeddings must be a finite matrix.")
    if np.any(np.linalg.norm(array, axis=1) == 0):
        raise ValueError("Cannot search with zero embeddings.")
    faiss.normalize_L2(array)
    return array


class CandidateIndex:
    def __init__(self, resumes: list[Resume], model=None):
        if not resumes:
            raise ValueError("Upload at least one readable resume.")
        self.resumes = {r.candidate_id: r for r in resumes}
        self.chunks = []
        # Short overlapping chunks reduce truncation by MiniLM's 256-token limit.
        for resume in self.resumes.values():
            for page, text in enumerate(resume.pages, 1):
                words = professional_text(text, first_page=(page == 1)).split()
                for start in range(0, len(words), 75):
                    chunk = " ".join(words[start:start + 100])
                    if chunk:
                        self.chunks.append({"candidate_id": resume.candidate_id,
                            "filename": resume.filename, "page": page, "text": chunk,
                            "citation": f"[{resume.candidate_id}, p.{page}]"})
        if not self.chunks:
            raise ValueError("No text available to index.")
        if len(self.chunks) > 2000:
            raise ValueError("Index exceeds 2,000 evidence chunks. Use a smaller batch.")
        self.model = model if model is not None else load_model()
        vectors = normalize(self.model.encode([c["text"] for c in self.chunks],
                            batch_size=16, convert_to_numpy=True, normalize_embeddings=True))
        self.index = faiss.IndexFlatIP(vectors.shape[1])
        self.index.add(vectors)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        validate_query(query)
        if not query.strip():
            raise ValueError("Enter a nonempty search or job description.")
        if not 1 <= top_k <= 50:
            raise ValueError("top_k must be between 1 and 50.")
        if len(query) > 20_000:
            raise ValueError("Query exceeds 20,000 characters.")
        words = query.split()
        parts = [" ".join(words[i:i + 100]) for i in range(0, len(words), 100)]
        query_vectors = normalize(self.model.encode(parts, convert_to_numpy=True,
                                                   normalize_embeddings=True))
        vector = normalize(query_vectors.mean(axis=0, keepdims=True))
        scores, indices = self.index.search(vector, len(self.chunks))
        results = {}
        for score, idx in zip(scores[0], indices[0]):
            chunk = self.chunks[int(idx)]
            cid = chunk["candidate_id"]
            if cid not in results:
                results[cid] = {**chunk, "similarity": float(np.clip(score, -1, 1))}
        return sorted(results.values(), key=lambda r: (-r["similarity"], r["candidate_id"]))[:top_k]


def requirement_evidence(resume: Resume, job_description: str) -> dict:
    """Conservative lexical evidence, not an unsupported semantic skill judgment."""
    if not job_description.strip() or len(job_description) > 20_000:
        raise ValueError("Provide a job description of 1–20,000 characters.")
    requirements = [s.strip(" \t-*•") for s in re.split(r"[\n;]+", job_description) if s.strip()]
    return {"method": "Job-description lines with exact phrase evidence only. No match does not mean lack of ability.",
            "requirements": [{"requirement": req,
                "exact_phrase_evidence": [e for e in resume.evidence()
                    if " ".join(req.lower().split()) in " ".join(e["text"].lower().split())],
                "status": "requires evidence review"} for req in requirements],
            "resume_evidence": resume.evidence()}
