"""Bounded, in-memory PDF extraction with stable document/page references."""
from dataclasses import dataclass
import hashlib
from pathlib import Path
import pymupdf

MAX_BYTES = 10 * 1024 * 1024
MAX_PAGES = 30


class ResumeError(ValueError):
    pass


@dataclass(frozen=True)
class Resume:
    candidate_id: str
    filename: str
    pages: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    provenance: str = "Uploaded document; supplied by the user."

    @property
    def text(self) -> str:
        return "\n\n".join(self.pages)

    def evidence(self) -> list[dict]:
        return [{"citation": f"[{self.candidate_id}, p.{i}]", "page": i, "text": text}
                for i, text in enumerate(self.pages, 1) if text.strip()]


def parse_pdf(data: bytes, filename: str) -> Resume:
    if not data or len(data) > MAX_BYTES:
        raise ResumeError("PDF must be nonempty and at most 10 MB.")
    if not data.lstrip().startswith(b"%PDF-"):
        raise ResumeError("Invalid PDF file header.")
    try:
        with pymupdf.open(stream=data, filetype="pdf") as doc:
            if doc.needs_pass:
                raise ResumeError("Password-protected PDFs are not supported.")
            if not 1 <= len(doc) <= MAX_PAGES:
                raise ResumeError("PDF must contain 1–30 pages.")
            pages = tuple(page.get_text("text").strip() for page in doc)
    except ResumeError:
        raise
    except Exception as exc:
        raise ResumeError("Could not read this PDF; it may be corrupt.") from exc
    if not any(p.strip() for p in pages):
        raise ResumeError("Scanned or empty PDF: no extractable text. Upload a text-based PDF; OCR is not included.")
    warnings = tuple(f"Page {i} has no extractable text; image content was not analyzed."
                     for i, p in enumerate(pages, 1) if not p.strip())
    if sum(map(len, pages)) > 100_000:
        raise ResumeError("Extracted text exceeds the 100,000-character limit.")
    return Resume(hashlib.sha256(data).hexdigest()[:12], Path(filename).name, pages, warnings)
