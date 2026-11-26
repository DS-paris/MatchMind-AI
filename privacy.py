"""Conservative text minimization; this is not a certified anonymization system."""
import re

SENSITIVE = re.compile(r"\b(date of birth|dob|age|gender|sex|race|ethnicity|religion|"
                       r"marital|married|nationality|citizenship|disability|disabled|"
                       r"pregnan\w*|sexual orientation|pronouns|family status)\b", re.I)
CONTACT = re.compile(r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b|(?:\+?\d[\d ()-]{7,}\d)", re.I)
HEADINGS = re.compile(r"^(?:professional |project |work )?(?:experience|projects|skills|"
                      r"technical skills|education|summary|profile|qualifications|"
                      r"certifications|employment|achievements)\b", re.I)


def professional_text(text: str, first_page=False) -> str:
    lines = text.splitlines()
    # Discard identifying headers when a recognizable professional section exists.
    if first_page:
        start = next((i for i, line in enumerate(lines) if HEADINGS.search(line.strip())), None)
        if start is not None:
            lines = lines[start:]
    return "\n".join(CONTACT.sub("[contact removed]", line) for line in lines
                     if not SENSITIVE.search(line))


def validate_query(query: str):
    if SENSITIVE.search(query):
        raise ValueError("Use professional skills and experience only; sensitive-attribute queries are not supported.")
