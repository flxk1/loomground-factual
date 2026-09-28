# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""ROUND 4, factual leg: a norm's content clause (an infinitive/bare-verb clause
with no subject of its own) lowers to an s/p/o claim with a subject supplied
out of band, via ``produce(sentence, context)``'s ``context['subject']``.

This path activates *only* when ``context['subject']`` is a non-empty string:
every other input (no context, an empty dict, a missing key, an empty or
non-string subject) must leave the sentence exactly as before -- ``[]`` for a
bare content clause, since it carries none of the grammar's own cues. It must
never fall back to fabricating a subject from the clause itself (there is
none) or from a bearer default.

The three literal cases below are the contract's regression pins, reported
for the versum leg to pin against. Dimension is RELATIONAL for all three: the
content clause's relation is always "predication" (``binding.json``'s entry
for any predicate that is not is-a/part-of/has-part or a temporal ordering).
"""
from __future__ import annotations

import pytest

from loomground_factual.plane import binding, produce
from loomground_factual.grammar import _content_clause

# --- the three required literal content clauses --------------------------------

MAKE = "make a solely automated decision on a credit application"
USE = "use the score to prepare a decision"
EXAMINE = "examine every rejection"


@pytest.mark.parametrize("clause,subject,predicate,obj", [
    (MAKE, "controller", "make", "solely automated decision on a credit application"),
    (USE, "controller", "use", "score to prepare a decision"),
    (EXAMINE, "reviewer", "examine", "every rejection"),
])
def test_content_clause_lowers_with_context_subject(clause, subject, predicate, obj):
    claims = produce(clause, {"subject": subject})
    assert len(claims) == 1, claims
    c = claims[0]
    co = c["coordinates"]
    assert (co["subject"], co["predicate"], co["object"]) == (subject, predicate, obj)
    assert c["relation"] == "predication"
    # the plane's own dimension binding (rules 1, 2): read from binding.json at
    # call time, never a hand-copied literal in this test module
    assert binding()[c["relation"]] == "relational"


def test_content_clause_dimension_is_relational_for_all_three():
    for clause, subject in [(MAKE, "controller"), (USE, "controller"),
                             (EXAMINE, "reviewer")]:
        c = produce(clause, {"subject": subject})[0]
        assert binding()[c["relation"]] == "relational"


# --- without context['subject'], behaves exactly as before ---------------------

@pytest.mark.parametrize("clause", [MAKE, USE, EXAMINE])
def test_bare_content_clause_without_context_is_unchanged(clause):
    assert produce(clause) == []
    assert produce(clause, None) == []
    assert produce(clause, {}) == []


# --- mutation-style: wrong or missing subject never silently substitutes -------

@pytest.mark.parametrize("context", [
    None,
    {},
    {"subject": ""},
    {"subject": None},
    {"subject": 123},
    {"subject": []},
    {"other": "controller"},
])
def test_missing_or_wrong_subject_context_does_not_lower(context):
    assert produce(MAKE, context) == []
    assert produce(EXAMINE, context) == []


def test_wrong_subject_yields_that_subject_not_a_default():
    # a caller-supplied subject is used verbatim; it is never overridden with
    # a hardcoded/default bearer such as "controller"
    claims = produce(EXAMINE, {"subject": "auditor"})
    assert claims[0]["coordinates"]["subject"] == "auditor"
    assert claims[0]["coordinates"]["subject"] != "controller"


def test_content_clause_helper_rejects_a_clause_with_its_own_cue():
    # a sentence that already has a copula/ordering/modal cue is not a content
    # clause: _content_clause must not intercept it even with a subject given
    assert _content_clause("The bank is a controller.", "controller") is None


def test_content_clause_helper_rejects_no_verb_or_empty_object():
    assert _content_clause("", "controller") is None
    # the sole token is consumed as the "verb", leaving no object at all
    assert _content_clause("the", "controller") is None
    # ROUND 5 fix: "the" is a determiner, not a bare verb -- the clause opens
    # with its own subject NP, so this abstains rather than treating "the" as
    # the verb and "credit application" as the object (round 4's behaviour)
    assert _content_clause("the credit application", "controller") is None


# --- existing outputs unchanged (acceptance 3, 4) -------------------------------

S1 = "The bank is a controller."
S2 = "The scoring model is part of the credit system."
S5 = "The controller knows that the training data is inaccurate."
S7 = "The review follows the automated scoring."


@pytest.mark.parametrize("sentence", [S1, S2, S5, S7])
def test_credit_case_outputs_unchanged_by_context_subject(sentence):
    baseline = produce(sentence)
    assert produce(sentence, {"subject": "controller"}) == baseline
    assert produce(sentence, {"subject": "someone-else"}) == baseline
    assert produce(sentence, None) == baseline


def test_s2_structural_output_is_exactly_unchanged():
    c = produce(S2, {"subject": "controller"})[0]
    co = c["coordinates"]
    assert (co["subject"], co["predicate"], co["object"]) == (
        "scoring model", "part of", "credit system")
    assert binding()[c["relation"]] == "structural"


def test_s7_precedes_output_is_exactly_unchanged():
    c = produce(S7, {"subject": "controller"})[0]
    co = c["coordinates"]
    assert (co["subject"], co["predicate"], co["object"]) == (
        "automated scoring", "precedes", "review")
    assert binding()[c["relation"]] == "temporal"


def test_s5_embedded_fact_output_is_exactly_unchanged():
    c = produce(S5, {"subject": "controller"})[0]
    co = c["coordinates"]
    assert (co["subject"], co["predicate"], co["object"]) == (
        "training data", "is", "inaccurate")
