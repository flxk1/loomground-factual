# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""ROUND 5, factual leg: the content-clause path (``produce(sentence, context)``
with ``context['subject']``) is an ACTION TYPE, not an asserted fact, and three
further fixes to the round-4 shape:

1. the claim carries ``asserted: False`` / ``entry_kind: "action_type"`` and an
   accurate method label (never the plain "lower" label an asserted fact gets);
2. a clause opening with "not"/"never" keeps negative polarity on that
   action-type output (round 4 mis-read the negation word itself as the verb);
3. a clause that carries its own subject NP is never forced through this path
   with the context subject substituted in -- it abstains instead.

Each test below is written to fail against the round-4 code (see the inline
"round 4" note on each), i.e. it is a revert probe for its fix.
"""
from __future__ import annotations

import pytest

from loomground_factual.plane import METHOD, METHOD_ACTION_TYPE, produce
from loomground_factual.grammar import _content_clause

MAKE = "make a solely automated decision on a credit application"
USE = "use the score to prepare a decision"
EXAMINE = "examine every rejection"


# --- fix 1: action-type flags + accurate method label ---------------------------

@pytest.mark.parametrize("clause,subject", [
    (MAKE, "controller"),
    (USE, "controller"),
    (EXAMINE, "reviewer"),
])
def test_content_path_claim_is_flagged_as_an_action_type_not_an_asserted_fact(clause, subject):
    c = produce(clause, {"subject": subject})[0]
    # round 4: no "asserted" / "entry_kind" key at all, and method ==
    # "loomground-factual/lower" -- the same label an asserted fact gets
    assert c["asserted"] is False
    assert c["entry_kind"] == "action_type"
    assert c["method"] == METHOD_ACTION_TYPE
    assert c["method"] != METHOD
    assert c["method"] != "loomground-factual/lower"


def test_asserted_paths_carry_no_action_type_flag():
    # an ordinary asserted claim (no context, or context ignored because the
    # sentence already lowers on its own) must never pick up the action-type
    # shape: no "asserted" key, no "entry_kind" key, plain method label
    c = produce("The bank is a controller.")[0]
    assert "asserted" not in c
    assert "entry_kind" not in c
    assert c["method"] == METHOD == "loomground-factual/lower"


# --- fix 2: not/never keeps negative polarity on the action-type output --------

NOT_CLAUSE = "not disclose the source of the score"
NEVER_CLAUSE = "never disclose the source of the score"


@pytest.mark.parametrize("clause", [NOT_CLAUSE, NEVER_CLAUSE])
def test_leading_not_never_keeps_negative_polarity(clause):
    # round 4: "not"/"never" is read by _VERB as the clause's own bare verb
    # (predicate == "not"/"never"), the real verb "disclose" ends up folded
    # into the object, and polarity comes out affirmative
    claims = produce(clause, {"subject": "controller"})
    assert len(claims) == 1, claims
    c = claims[0]
    co = c["coordinates"]
    assert co["predicate"] == "disclose"
    assert co["subject"] == "controller"
    assert "source of the score" in co["object"]
    assert co["polarity"] == "negative"
    assert c["asserted"] is False
    assert c["entry_kind"] == "action_type"


def test_content_clause_helper_reports_negated_true_for_not_never():
    rec = _content_clause(NOT_CLAUSE, "controller")
    assert rec is not None
    assert rec["fact"]["negated"] is True
    rec2 = _content_clause(NEVER_CLAUSE, "controller")
    assert rec2 is not None
    assert rec2["fact"]["negated"] is True


# --- fix 3: a clause with its own subject never takes the context subject -----

OWN_SUBJECT_CLAUSES = [
    "the court orders otherwise",
    "the data protection authority objects",
    "a reviewer intervenes",
]


@pytest.mark.parametrize("clause", OWN_SUBJECT_CLAUSES)
def test_own_subject_clause_abstains_rather_than_take_context_subject(clause):
    # round 4: the leading determiner ("the"/"a") is read as the bare verb,
    # and the context subject ("controller") is spliced onto a clause whose
    # own subject is someone else entirely (the court, the authority, a
    # reviewer) -- exactly the bearer-substitution bug this fix closes
    claims = produce(clause, {"subject": "controller"})
    assert claims == []
    assert _content_clause(clause, "controller") is None


def test_own_subject_clause_helper_abstains_directly():
    assert _content_clause("the court orders otherwise", "controller") is None
    assert _content_clause("a reviewer intervenes", "controller") is None


def test_own_subject_with_leading_negation_still_abstains():
    # a leading "not"/"never" is stripped first, but the clause still opens
    # with its own subject NP underneath -- must still abstain, not borrow
    # the context subject for what remains
    assert _content_clause("not the court orders otherwise", "controller") is None


# --- fix 4 (documentation/consistency): relation/dimension is always the
# action type's own "predication" -> relational, never inherited -----------------

@pytest.mark.parametrize("clause,subject", [
    (MAKE, "controller"),
    (NOT_CLAUSE, "controller"),
])
def test_action_type_relation_and_dimension_are_always_predication_relational(clause, subject):
    from loomground_factual.plane import binding
    c = produce(clause, {"subject": subject})[0]
    assert c["relation"] == "predication"
    assert binding()[c["relation"]] == "relational"
