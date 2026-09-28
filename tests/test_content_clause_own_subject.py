# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""ROUND 5, factual leg, defect (b): a content clause that carries its OWN
subject -- a closed pronoun ("they", "it", "he", "she", "we") or a multi-word
Title-Case named subject (e.g. "Member States") -- keeps that subject, never
the enclosing/context subject, and the predicate never begins with or
contains the subject token. A subjectless (bare-verb/infinitive) clause keeps
inheriting the context subject exactly as before (no regression).

Each literal test below is written to fail against the pre-fix code (see the
inline "pre-fix" note on each): a revert probe for this round's fix.
"""
from __future__ import annotations

import pytest

from loomground_factual.plane import METHOD_ACTION_TYPE, produce
from loomground_factual.grammar import _content_clause

# --- own subject: pronoun --------------------------------------------------

THEY_CLAUSE = "they notify the data subject without delay"
IT_CLAUSE = "it concerns only the automated part of the decision"

# --- own subject: named (multi-word Title-Case) NP -------------------------

MEMBER_STATES_CLAUSE = "Member States lay down the rules on penalties applicable to infringements"

# --- subjectless: keeps inheriting the context subject ----------------------

EXAMINE = "examine every rejection"


def test_they_clause_keeps_its_own_subject_not_the_context_subject():
    # pre-fix: "they" is read as the bare verb (predicate == "they"), the real
    # verb "notify" is folded into the object, and the context subject
    # ("controller") is spliced on in place of "they"
    claims = produce(THEY_CLAUSE, {"subject": "controller"})
    assert len(claims) == 1, claims
    co = claims[0]["coordinates"]
    assert co["subject"] == "they"
    assert co["subject"] != "controller"
    assert co["predicate"] == "notify"
    assert "they" not in co["predicate"]
    assert co["object"] == "data subject without delay"
    assert claims[0]["asserted"] is False
    assert claims[0]["method"] == METHOD_ACTION_TYPE


def test_it_clause_keeps_its_own_subject_not_the_context_subject():
    # pre-fix: "it" is read as the bare verb (predicate == "it"), and the
    # context subject ("controller") is spliced on in place of "it"
    claims = produce(IT_CLAUSE, {"subject": "controller"})
    assert len(claims) == 1, claims
    co = claims[0]["coordinates"]
    assert co["subject"] == "it"
    assert co["subject"] != "controller"
    assert co["predicate"] == "concerns"
    assert "it" not in co["predicate"]
    assert co["object"] == "only the automated part of the decision"


def test_member_states_clause_keeps_its_own_subject_not_the_context_subject():
    # pre-fix: "Member" (a single alpha token) is read as the bare verb, the
    # rest ("States lay down ...") is folded into the object, and the
    # context subject ("controller") is spliced on in place of "Member States"
    claims = produce(MEMBER_STATES_CLAUSE, {"subject": "controller"})
    assert len(claims) == 1, claims
    co = claims[0]["coordinates"]
    assert co["subject"] == "Member States"
    assert co["subject"] != "controller"
    assert co["predicate"] == "lay"
    assert "member" not in co["predicate"].lower()
    assert "states" not in co["predicate"].lower()
    assert co["object"] == "down the rules on penalties applicable to infringements"


@pytest.mark.parametrize("clause,own_subject,predicate,fragment", [
    (THEY_CLAUSE, "they", "notify", "data subject"),
    (IT_CLAUSE, "it", "concerns", "automated part"),
    (MEMBER_STATES_CLAUSE, "Member States", "lay", "rules on penalties"),
])
def test_helper_reports_own_subject_directly(clause, own_subject, predicate, fragment):
    rec = _content_clause(clause, "controller")
    assert rec is not None, rec
    fact = rec["fact"]
    assert fact["subject"] == own_subject
    assert fact["subject"] != "controller"
    assert fact["predicate"] == predicate
    assert own_subject.lower() not in fact["predicate"].lower()
    assert fragment in fact["object"]


# --- subjectless clause: unchanged, still inherits the context subject -----

def test_subjectless_clause_still_inherits_the_context_subject():
    claims = produce(EXAMINE, {"subject": "reviewer"})
    assert len(claims) == 1, claims
    co = claims[0]["coordinates"]
    assert co["subject"] == "reviewer"
    assert co["predicate"] == "examine"
    assert co["object"] == "every rejection"


def test_subjectless_clause_helper_still_inherits_the_context_subject():
    rec = _content_clause(EXAMINE, "reviewer")
    assert rec is not None
    assert rec["fact"]["subject"] == "reviewer"
    assert rec["fact"]["predicate"] == "examine"


# --- determiner-led common-noun own-subject clauses still abstain (no
# regression on the round-4 behaviour this round leaves untouched) ----------

@pytest.mark.parametrize("clause", [
    "the court orders otherwise",
    "a reviewer intervenes",
    "the data protection authority objects",
])
def test_determiner_led_own_subject_clause_still_abstains(clause):
    assert produce(clause, {"subject": "controller"}) == []
    assert _content_clause(clause, "controller") is None
