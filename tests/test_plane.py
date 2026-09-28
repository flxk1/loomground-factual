# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Plane descriptor contract v1 for the factual plane, and the credit-decision case.

Each test names the plane-fit rule it proves (PORT-PLAN "Plane fit: 100%").
"""
from __future__ import annotations

import json
import re
from importlib.metadata import entry_points
from importlib.resources import files
from pathlib import Path

import pytest

import loomground_factual
from loomground_factual import lower
from loomground_factual.grammar import load_json
from loomground_factual.plane import SLOTS, plane, produce

FIVE = {"structural", "causal", "intentional", "temporal", "relational"}
PKG = Path(loomground_factual.__file__).resolve().parent

S1 = "The bank is a controller."
S2 = "The scoring model is part of the credit system."
S3 = "The controller must not make a solely automated decision on a credit application."
S4 = "The controller may use the score to prepare a decision."
S5 = "The controller knows that the training data is inaccurate."
S6 = "A reviewer shall examine every rejection before it is sent."
S7 = "The review follows the automated scoring."


def _text(sentence, span):
    return sentence[span[0]:span[1]]


def _one(sentence):
    claims = produce(sentence)
    assert len(claims) == 1, claims
    return claims[0]


# --- the credit-decision case, sentence by sentence ---------------------------

def test_s1_is_a_structural():
    f = lower(S1)
    assert f == {"subject": "bank", "predicate": "is", "object": "controller",
                 "dimension": "structural", "negated": False,
                 "quantification": "existential"}
    c = _one(S1)
    assert c["relation"] == "is-a"
    assert _text(S1, c["span"]) == "The bank is a controller"


def test_s2_keeps_part_of_as_predicate():
    f = lower(S2)
    assert (f["subject"], f["predicate"], f["object"]) == (
        "scoring model", "part of", "credit system")
    assert f["dimension"] == "structural"
    assert _one(S2)["relation"] == "part-of"


@pytest.mark.parametrize("sentence,subject,predicate,obj,negated", [
    (S3, "controller", "make", "solely automated decision on a credit application", True),
    (S4, "controller", "use", "score to prepare a decision", False),
    (S6, "reviewer", "examine", "every rejection", False),
])
def test_modal_sentences_lower_to_propositional_content(sentence, subject, predicate,
                                                        obj, negated):
    f = lower(sentence)
    assert f is not None, "modal sentence must lower (was None / mis-lowered)"
    assert (f["subject"], f["predicate"], f["object"]) == (subject, predicate, obj)
    assert f["negated"] is negated
    assert f["dimension"] == "relational"
    # the modal auxiliary is stripped: it is not the predicate, nor in subject/object
    for modal in ("must", "may", "shall"):
        assert modal not in f["predicate"].split()
        assert modal not in f["subject"].split()
    c = _one(sentence)
    assert _text(sentence, c["span"]) == sentence.rstrip(".")


def test_s6_not_mislowered_on_subordinate_copula():
    # the "is" inside "before it is sent" is not the fact's copula
    f = lower(S6)
    assert f["predicate"] == "examine" and "it" not in f["subject"]
    link, = _one(S6)["links"]
    assert link == {"type": "temporal", "relation": "precedes",
                    "to_span": link["to_span"]}
    assert _text(S6, link["to_span"]) == "it is sent"


def test_s5_embedded_clause_is_its_own_fact_with_sub_span():
    f = lower(S5)
    assert (f["subject"], f["predicate"], f["object"]) == (
        "training data", "is", "inaccurate")
    assert "knows" not in f["subject"] and "controller" not in f["subject"]
    c = _one(S5)
    assert _text(S5, c["span"]) == "the training data is inaccurate"
    assert c["span"] != [0, len(S5) - 1]      # a sub-span, not the attitude


def test_s7_yields_precedes_ordering_as_temporal_claim():
    f = lower(S7)
    assert (f["subject"], f["predicate"], f["object"], f["dimension"]) == (
        "review", "follows", "automated scoring", "temporal")
    c = _one(S7)
    assert c["relation"] == "precedes"
    assert plane()["binding"][c["relation"]] == "temporal"
    co = c["coordinates"]
    assert (co["subject"], co["predicate"], co["object"]) == (
        "automated scoring", "precedes", "review")


def test_not_applicable_is_empty_list():
    assert produce("Where possible, act promptly.") == []
    assert produce("") == []
    assert produce(None) == []  # type: ignore[arg-type]


# --- descriptor contract v1 ----------------------------------------------------

def test_entry_point_discovers_factual_plane():
    eps = {ep.name: ep for ep in entry_points(group="loomground.planes")}
    assert "factual" in eps, "reinstall with pip install --no-deps -e ."
    d = eps["factual"].load()()
    assert d["plane"] == "factual"
    assert set(d) >= {"plane", "language_version", "nd_system", "binding", "produce"}
    assert callable(d["produce"])


def test_version_locked_to_package_version():
    # rule 5
    d = plane()
    assert d["language_version"] == loomground_factual.__version__
    assert d["nd_system"]["version"] == d["language_version"]
    assert not any(k.endswith("_5d_version") for k in d["nd_system"])


def test_nd_system_validates_in_versum():
    nd = pytest.importorskip("versum.nd")
    d = plane()
    system = nd.NDSystem.from_dict(d["nd_system"]).validate()
    assert system.version == d["language_version"]
    assert set(system.axes) == {"subject", "predicate", "object", "polarity",
                                "quantification"}
    assert system.unknown_values == "reject"


def test_every_produced_claim_fits_the_nd_system_fail_closed():
    # rules 4 and 6: every coordinate is accepted by its axis; a foreign value is
    # rejected by the consumer, never repaired by the producer
    nd = pytest.importorskip("versum.nd")
    d = plane()
    system = nd.NDSystem.from_dict(d["nd_system"]).validate()
    rules = {r.form_slot: r for r in system.bindings}
    for ex in d["examples"]:
        for c in produce(ex["sentence"]):
            for axis, value in c["coordinates"].items():
                assert system.axes[axis].validate_value(value) == [], (axis, value)
            for slot, axis in c["slots"].items():
                assert axis in rules[slot].allowed_axes
    assert system.axes["polarity"].validate_value("maybe")
    assert system.axes["quantification"].validate_value("most")


def test_binding_is_five_dimensions_from_one_data_file():
    # rules 2 and 3
    d = plane()
    assert d["binding"] and set(d["binding"].values()) <= FIVE
    art = files("loomground_factual") / "artifacts"
    holders = [p.name for p in art.iterdir() if p.name.endswith(".json")
               and "binding" in json.loads(p.read_text("utf-8"))]
    assert holders == ["binding.json"]
    assert d["binding"] == json.loads((art / "binding.json").read_text("utf-8"))["binding"]
    # no dict literal of it in code: no dimension name is a string literal in .py
    for py in PKG.rglob("*.py"):
        src = py.read_text("utf-8")
        for dim in FIVE:
            assert not re.search(rf"[\"']{dim}[\"']", src), (py.name, dim)
    # every relation the grammar can emit is bound
    ex = load_json("extraction.json")
    emitted = (set(ex["predicate_cues"]["relations"]) | set(ex["ordering_cues"])
               | {c["canonical"] for c in ex["ordering_cues"].values()}
               | {ex["predicate_cues"]["default_relation"]}
               | set(ex["modal_cues"]["temporal_subordinate"]))
    assert emitted <= set(d["binding"])


def test_vocabularies_derived_from_grammar_artifacts():
    # rule 1: closed vocabularies equal the grammar source, not literals
    ex = load_json("extraction.json")
    axes = plane()["nd_system"]["axes"]
    assert axes["quantification"]["vocabulary"] == list(ex["quantifier_cues"])
    assert axes["polarity"]["vocabulary"] == list(ex["polarity_values"])
    for axis in ("polarity", "quantification"):
        assert axes[axis]["vocabulary_mode"] == "closed"
    # the slots the producer fills are exactly the nD system's binding rules
    rules = {r["form_slot"]: r["allowed_axes"] for r in plane()["nd_system"]["bindings"]}
    assert {s: [a] for s, a in SLOTS.items()} == rules


def test_round_trip_published_examples():
    # rule 4: every published conformance vector reproduces field for field
    exs = plane()["examples"]
    assert len(exs) >= 7
    for ex in exs:
        assert produce(ex["sentence"]) == ex["expected"], ex["sentence"]
        for c in ex["expected"]:
            s0, s1 = c["span"]
            assert 0 <= s0 < s1 <= len(ex["sentence"])


def test_produce_is_deterministic_and_context_free():
    assert produce(S7) == produce(S7, context={"source": "x"}) == produce(S7)


def test_package_never_imports_versum():
    for py in PKG.rglob("*.py"):
        assert not re.search(r"^\s*(?:from|import)\s+versum\b", py.read_text("utf-8"), re.M)
