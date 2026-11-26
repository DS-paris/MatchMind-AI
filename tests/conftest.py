import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pytest
from parser import Resume
from matcher import CandidateIndex


class TinyEncoder:
    """Deterministic test double; production always uses Sentence Transformers."""
    def encode(self, texts, **kwargs):
        return np.array([[1 + text.lower().count("python"),
                          1 + text.lower().count("react"), 1] for text in texts], dtype="float32")


@pytest.fixture
def candidate_index():
    return CandidateIndex([Resume("alpha", "alpha.pdf", ("Python Python Python machine learning",)),
                           Resume("beta", "beta.pdf", ("React React React web development",))], TinyEncoder())
