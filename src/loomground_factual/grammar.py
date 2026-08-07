# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Factual language: lower a free-text assertion into a fixed-5D edge.

A fact is a relation between entities, so it lowers straight onto the 5D floor —
no nD facet. ``is-a``/``part-of`` -> STRUCTURAL; any other predicate ->
RELATIONAL; polarity and quantification ride as edge properties. ``clean_entity``
is the shared NP-head primitive the modal languages (deontic bearer, epistemic
holder) consume, so the addressee vocabulary lives in one place. Standard library
only; cues are DATA in ``artifacts/extraction.json``.
"""
from __future__ import annotations

import json
import re
from importlib.resources import files
from typing import Any, Optional

__all__ = ["load_json", "clean_entity", "lower"]


def load_json(name: str) -> Any:
    return json.loads((files("loomground_factual") / "artifacts" / name).read_text("utf-8"))


_EX = load_json("extraction.json")
_STRUCT = re.compile(_EX["predicate_cues"]["structural"], re.I)
_COP = re.compile(_EX["predicate_cues"]["copula"], re.I)
_NEG = re.compile(_EX["polarity_cues"]["negation"], re.I)
_UNIV = re.compile(_EX["quantifier_cues"]["universal"], re.I)
_EMPTY = re.compile(_EX["quantifier_cues"]["empty"], re.I)
_MARKERS = re.compile(_EX["entity_cues"]["entity_markers"], re.I)
_LEAD = re.compile(_EX["entity_cues"]["entity_lead"], re.I)
_TRAIL = re.compile(_EX["entity_cues"]["entity_trail"], re.I)
_OBJ_LEAD = re.compile(r"^(?:not\s+)?(?:a|an|the|one of(?: the)?|part of)\s+", re.I)


def clean_entity(span: str) -> str:
    """Reduce a span to its addressee/entity NP head: strip list/paragraph markers,
    take the NP after the last comma of a subordinate lead-in, drop a leading
    determiner/quantifier. Shared by deontic (bearer) and epistemic (holder)."""
    s = _MARKERS.sub("", (span or "").strip()).strip()
    if "," in s:
        s = s.rsplit(",", 1)[-1].strip()
    s = _LEAD.sub("", s).strip()
    s = _TRAIL.sub("", s).strip()   # drop a trailing relative/qualifier clause
    return s.strip(" .,;:")


def lower(sentence: str) -> Optional[dict[str, Any]]:
    """Lower an assertion into a 5D edge, or ``None`` when no copula is present."""
    if not isinstance(sentence, str) or not sentence.strip():
        return None
    m = _COP.search(sentence)
    if not m:
        return None
    subj_raw = sentence[:m.start()]
    obj_raw = sentence[m.end():].strip()
    dimension = "structural" if _STRUCT.search(sentence) else "relational"
    obj = _OBJ_LEAD.sub("", obj_raw).strip(" .,;:")
    if _EMPTY.search(subj_raw):
        quant = "empty"
    elif _UNIV.search(subj_raw):
        quant = "universal"
    else:
        quant = "existential"
    # an empty-quantifier subject ("no provider …") is itself a negative claim,
    # as is an object-side negation ("… is not a …").
    negated = quant == "empty" or bool(_NEG.search(obj_raw[:24]))
    subject = clean_entity(subj_raw)
    if not subject or not obj:
        return None
    return {
        "subject": subject,
        "predicate": m.group(0).strip().lower(),
        "object": obj,
        "dimension": dimension,      # RELATIONAL floor or STRUCTURAL (is-a/part-of)
        "negated": negated,
        "quantification": quant,
    }
