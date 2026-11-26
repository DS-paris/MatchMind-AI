import pymupdf
import pytest
from parser import parse_pdf, ResumeError, MAX_BYTES


def pdf_bytes(text=None, blank_page=False):
    with pymupdf.open() as doc:
        page = doc.new_page()
        if text:
            page.insert_text((72, 72), text)
        if blank_page:
            doc.new_page()
        return doc.tobytes()


def test_parse_and_cite():
    data = pdf_bytes("Python developer", blank_page=True)
    resume = parse_pdf(data, "resume.pdf")
    assert "Python developer" in resume.text
    assert resume.evidence()[0]["citation"] == f"[{resume.candidate_id}, p.1]"
    assert resume.warnings
    assert resume.candidate_id == parse_pdf(data, "renamed.pdf").candidate_id


@pytest.mark.parametrize("data", [b"", b"not a pdf", b"%PDF-broken", b"x" * (MAX_BYTES + 1)])
def test_invalid_pdf(data):
    with pytest.raises(ResumeError):
        parse_pdf(data, "bad.pdf")


def test_empty_pdf():
    with pytest.raises(ResumeError, match="Scanned or empty"):
        parse_pdf(pdf_bytes(), "scan.pdf")


def test_encrypted_pdf():
    with pymupdf.open() as doc:
        doc.new_page().insert_text((72, 72), "Python")
        data = doc.tobytes(encryption=pymupdf.PDF_ENCRYPT_AES_256, owner_pw="owner", user_pw="user")
    with pytest.raises(ResumeError, match="Password"):
        parse_pdf(data, "secret.pdf")
