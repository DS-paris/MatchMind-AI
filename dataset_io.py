"""Source-specific ingestion. No scraped mirrors or synthetic records are accepted."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re
from parser import Resume
from privacy import professional_text

ROOT = Path(__file__).resolve().parent
LOCAL = ROOT / "data" / "private"
RESUME_SOURCE = "https://huggingface.co/datasets/Careerflow/ResumeBench"
REVISION = "db07f5ad52c061784f5728a4ded1e356e4b59278"
BLOCKER = "ResumeBench download returned HTTP 401: authenticated access and acceptance of publisher conditions are required. No real resumes have been imported."
ONET_ATTRIBUTION = ("Includes adapted O*NET® 31.0 Database information from USDOL/ETA, "
                    "under CC BY 4.0. MatchMind selected and reformatted fields. "
                    "USDOL/ETA has not approved, endorsed, or tested these modifications.")


def preprocess_records(records):
    """Keep real-anonymized records and job-relevant source fields only.

    This is minimization, not guaranteed anonymization. Review before activation.
    Source field values are preserved except explicit PII redactions.
    """
    stats = dict(input_records=0, excluded_non_real=0, excluded_empty=0,
                 duplicates=0, retained=0, removed_characters=0)
    resumes, seen = [], set()
    for record in records:
        stats["input_records"] += 1
        if record.get("source") != "real-anonymized":
            stats["excluded_non_real"] += 1
            continue
        truth = record.get("ground_truth", {})
        basics = truth.get("basics", {}) or {}
        identifiers = [str(v) for v in basics.values() if isinstance(v, (str, int)) and len(str(v)) > 2]
        sections = []
        # Drop basics, summaries, employers, institutions, dates, locations,
        # personal profiles, interests, and unconstrained custom sections.
        for section, fields in {"skills": ("category", "skills"),
                                "experience": ("position", "description"),
                                "education": ("area", "studyType"),
                                "projects": ("description",)}.items():
            values = []
            content = truth.get(section, {}) or {}
            if not isinstance(content, dict):
                continue
            for item in content.get("items", []):
                if not isinstance(item, dict):
                    continue
                for field in fields:
                    value = item.get(field)
                    strings = value if isinstance(value, list) else [value]
                    values.extend(s for s in strings if isinstance(s, str))
            if values:
                sections.append(section.upper() + "\n" + "\n".join(values))
        raw = "\n\n".join(sections)
        text = raw
        for identifier in sorted(identifiers, key=len, reverse=True):
            text = re.sub(re.escape(identifier), "[identity removed]", text, flags=re.I)
        text = re.sub(r"https?://\S+|www\.\S+", "[URL removed]", text)
        text = professional_text(text)
        stats["removed_characters"] += max(0, len(raw) - len(text))
        if len(text.split()) < 8:
            stats["excluded_empty"] += 1
            continue
        digest = hashlib.sha256(text.encode()).hexdigest()
        if digest in seen:
            stats["duplicates"] += 1
            continue
        seen.add(digest)
        source_id = str(record.get("resume_id", ""))
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", source_id):
            raise ValueError("Invalid source record ID.")
        resumes.append(Resume(digest[:12], f"ResumeBench-{digest[:12]}", (text,),
            provenance=f"{RESUME_SOURCE}/blob/{REVISION}/test.jsonl — record {source_id}; "
                       "p.1 denotes a structured source extract, not original PDF pagination; CC BY 4.0"))
    stats["retained"] = len(resumes)
    return resumes, stats


def write_staged(records, revision=REVISION, folder=LOCAL):
    resumes, stats = preprocess_records(records)
    if not resumes:
        raise ValueError("No usable real-anonymized records; nothing was activated.")
    folder.mkdir(parents=True, exist_ok=True)
    payload = {"source": RESUME_SOURCE, "revision": revision, "license": "CC BY 4.0",
               "stats": stats, "resumes": [asdict(r) for r in resumes]}
    path = folder / "resumebench.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    # Any new import invalidates prior manual review.
    (folder / "review.sha256").unlink(missing_ok=True)
    return path


def load_real_dataset(folder=LOCAL):
    path = folder / "resumebench.json"
    if not path.exists():
        raise ValueError(BLOCKER)
    raw = path.read_bytes()
    marker = folder / "review.sha256"
    if not marker.exists() or marker.read_text().strip() != hashlib.sha256(raw).hexdigest():
        raise ValueError("Imported records require local privacy review. See README before activation.")
    payload = json.loads(raw)
    if (payload.get("source") != RESUME_SOURCE or payload.get("license") != "CC BY 4.0"
            or payload.get("revision") != REVISION):
        raise ValueError("Dataset provenance or license does not match the supported source.")
    return [Resume(**{**r, "pages": tuple(r["pages"]), "warnings": tuple(r["warnings"])})
            for r in payload["resumes"]], {k: v for k, v in payload.items() if k != "resumes"}


def load_occupations():
    path = ROOT / "data" / "onet_occupations.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def occupation_requirements(occupation):
    return "\n".join([occupation["title"], occupation["description"],
                      *occupation["skills"], *occupation["tasks"]])
