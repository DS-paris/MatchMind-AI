import pytest
from privacy import professional_text


def test_personal_fields_removed():
    text = "Jane Example\njane@example.com\nSKILLS\nPython\nAge: 28\nReligion: example"
    minimized = professional_text(text, first_page=True)
    assert "Python" in minimized
    assert "Jane" not in minimized
    assert "Age" not in minimized
    assert "Religion" not in minimized


def test_sensitive_query_refused(candidate_index):
    with pytest.raises(ValueError, match="sensitive"):
        candidate_index.search("rank by age")
