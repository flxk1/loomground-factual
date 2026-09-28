# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""A content clause's own-subject detection must not mistake a sentence-initial
CAPITALISED IMPERATIVE VERB for a named subject.

Two failure modes, both fixed here:

1. "Notify Member States without delay" / "Inform Data Subjects of the
   breach" -- a standalone imperative sentence, capitalised only because it
   opens a sentence. Pre-fix, ``_OWN_NAMED`` greedily consumed all three
   leading Title-Case words ("Notify Member States") as the subject, leaving
   "without"/"of" to be mis-read as the predicate and the context subject
   ("controller") discarded. Fixed: the leading verb is read as the
   predicate, "Member States"/"Data Subjects" stays in the object, and the
   context subject is kept.

2. "The Court orders otherwise" -- pre-fix, capitalising the determiner-led
   "the court" (only because it happens to open a sentence) made
   ``_OWN_NAMED`` treat "The Court" as a two-word named subject, producing a
   claim where the same sentence in lower case ("the court orders
   otherwise") abstains. Fixed: capitalisation of a determiner-led
   common-noun subject must never flip its abstention -- both variants take
   the identical path and return the identical (``None`` / ``[]``) result.

Own subjects genuinely belonging to the clause -- a pronoun, or a real
two-word Title-Case name not led by a determiner -- are unaffected and keep
working exactly as before this fix.
"""
from __future__ import annotations

import pytest

from loomground_factual.grammar import _content_clause
from loomground_factual.plane import produce

CONTEXT = {"subject": "controller"}


# --- fix (1): a sentence-initial capitalised imperative verb is not a named
# subject; the context subject is kept and the real named entity stays in
# the object ------------------------------------------------------------------

def test_notify_member_states_keeps_context_subject_and_notify_predicate():
    claims = produce("Notify Member States without delay", CONTEXT)
    assert len(claims) == 1, claims
    co = claims[0]["coordinates"]
    assert co["subject"] == "controller"
    assert co["predicate"] == "notify"
    assert "Member States" in co["object"]


def test_notify_member_states_helper_reports_context_subject_directly():
    rec = _content_clause("Notify Member States without delay", "controller")
    assert rec is not None, rec
    fact = rec["fact"]
    assert fact["subject"] == "controller"
    assert fact["predicate"] == "notify"
    assert "Member States" in fact["object"]


def test_inform_data_subjects_keeps_context_subject_and_inform_predicate():
    claims = produce("Inform Data Subjects of the breach", CONTEXT)
    assert len(claims) == 1, claims
    co = claims[0]["coordinates"]
    assert co["subject"] == "controller"
    assert co["predicate"] == "inform"
    assert "Data Subjects" in co["object"]


def test_inform_data_subjects_helper_reports_context_subject_directly():
    rec = _content_clause("Inform Data Subjects of the breach", "controller")
    assert rec is not None, rec
    fact = rec["fact"]
    assert fact["subject"] == "controller"
    assert fact["predicate"] == "inform"
    assert "Data Subjects" in fact["object"]


# --- own subjects are kept: pronoun, and a genuine two-word named subject
# not led by a determiner, both unaffected by this fix -------------------------

def test_they_disclose_keeps_its_own_pronoun_subject():
    claims = produce("They disclose the source of the score", CONTEXT)
    assert len(claims) == 1, claims
    co = claims[0]["coordinates"]
    assert co["subject"].lower() == "they"
    assert co["predicate"] == "disclose"
    assert co["subject"] != "controller"


def test_it_requires_keeps_its_own_pronoun_subject():
    claims = produce("It requires a review", CONTEXT)
    assert len(claims) == 1, claims
    co = claims[0]["coordinates"]
    assert co["subject"].lower() == "it"
    assert co["predicate"] == "requires"
    assert co["subject"] != "controller"


def test_member_states_ensure_keeps_its_own_named_subject():
    claims = produce("Member States ensure compliance with the rules", CONTEXT)
    assert len(claims) == 1, claims
    co = claims[0]["coordinates"]
    assert co["subject"] == "Member States"
    assert co["predicate"] == "ensure"
    assert co["subject"] != "controller"


# --- fix (2): capitalisation must not flip a determiner-led abstention -------

def test_capitalised_and_lowercase_court_variants_produce_the_identical_result():
    upper = produce("The Court orders otherwise", CONTEXT)
    lower = produce("the court orders otherwise", CONTEXT)
    assert upper == lower == []


def test_capitalised_and_lowercase_court_variants_helper_produce_the_identical_result():
    upper = _content_clause("The Court orders otherwise", "controller")
    lower = _content_clause("the court orders otherwise", "controller")
    assert upper == lower is None
