"""Portable Markdown exports including an auditable evidence appendix."""
import re


def safe_text(text):
    return re.sub(r"([\\`*_{}\[\]<>#|])", r"\\\1", str(text))


def build_report(index, results, job_description, messages=None, retrieval_query="", requirements_source=""):
    lines = ["# MatchMind AI — Recruitment Research", "",
             "Retrieval similarity is cosine similarity, not hiring suitability or a match percentage.",
             "Human review is required. Missing evidence does not establish missing ability.", "",
             "## Job description", safe_text(job_description), "",
             "## Retrieval query", safe_text(retrieval_query or job_description), "",
             "Candidate score is maximum chunk cosine similarity; no relevance threshold is applied.",
             "## Retrieval results"]
    if requirements_source:
        from dataset_io import ONET_ATTRIBUTION
        lines.extend(["## Occupational reference provenance", safe_text(requirements_source),
                      ONET_ATTRIBUTION, "https://www.onetcenter.org/database.html",
                      "License: https://creativecommons.org/licenses/by/4.0/",
                      "Requirements may have been edited by the user."])
    for row in results:
        lines.extend([f"- {safe_text(row['filename'])} ({row['candidate_id']}): {row['similarity']:.4f}",
                      f"  Evidence {row['citation']}: {safe_text(row['text'])}"])
    if messages:
        lines.extend(["", "## Assistant conversation (AI-generated; verify citations)"])
        for msg in messages:
            lines.extend([f"\n### {msg['role'].title()}", msg['content']])
    lines.extend(["", "## Source documents"])
    for resume in index.resumes.values():
        lines.append(f"\n### {resume.candidate_id} — {safe_text(resume.filename)}")
        lines.append(safe_text(resume.provenance))
        for evidence in resume.evidence():
            lines.extend([f"\n{evidence['citation']}", safe_text(evidence['text'])])
    return "\n\n".join(lines)
