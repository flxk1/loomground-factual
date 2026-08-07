# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Cross-jurisdiction quality gate for factual -> 5D lowering.

Each case is a real definitional/assertoric provision with the EXPECTED 5D edge.
This is the durable gate that guards extraction quality (structure tests never did).
"""
from __future__ import annotations

import re

from loomground_factual import lower


def _n(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower()).strip(" .,;:")


CASES = [
    # (raw, subject, dimension, negated, quantification)
    ("Biometric data is a special category of personal data.",
     "biometric data", "structural", False, "existential"),
    ("A processor is a natural or legal person which processes personal data on behalf of the controller.",
     "processor", "structural", False, "existential"),
    ("The AI system is not a high-risk AI system.",
     "ai system", "structural", True, "existential"),
    ("Personal data includes any information relating to an identified natural person.",
     "personal data", "relational", False, "existential"),
    ("All controllers are subject to this Regulation.",
     "controllers", "relational", False, "universal"),
    ("No provider is exempt from the transparency obligations.",
     "provider", "relational", True, "empty"),
]


def test_factual_lowers_into_5d():
    subj = dim = neg = quant = 0
    for raw, e_subj, e_dim, e_neg, e_quant in CASES:
        f = lower(raw) or {}
        subj += _n(f.get("subject", "")) == _n(e_subj)
        dim += f.get("dimension") == e_dim
        neg += f.get("negated") == e_neg
        quant += f.get("quantification") == e_quant
    n = len(CASES)
    # gate: subject + dimension + negation must be perfect; quantification >= n-1
    assert subj == n, f"subject {subj}/{n}"
    assert dim == n, f"dimension {dim}/{n}"
    assert neg == n, f"negation {neg}/{n}"
    assert quant >= n - 1, f"quantification {quant}/{n}"
