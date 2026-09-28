# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Cue tie-break (longest match at the same offset) and the ``cannot`` modal.

Every expected value here is a hand-written literal; none is read from the
packaged artifacts the grammar reads (G3).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from loomground_factual import lower
from loomground_factual.plane import produce


def test_is_required_to_strips_the_auxiliary():
    # the modal "is required to" beats the bare copula "is" at the same offset
    assert lower("A controller is required to notify the authority.") == {
        "subject": "controller", "predicate": "notify", "object": "authority",
        "dimension": "relational", "negated": False,
        "quantification": "existential"}


def test_are_required_to_strips_the_auxiliary():
    f = lower("All controllers are required to keep records.")
    assert (f["subject"], f["predicate"], f["object"]) == ("controllers", "keep", "records")
    assert f["quantification"] == "universal"


@pytest.mark.parametrize("sentence", [
    "The provider cannot refuse access.",
    "The provider can not refuse access.",
])
def test_cannot_lowers_as_negated_modal(sentence):
    assert lower(sentence) == {
        "subject": "provider", "predicate": "refuse", "object": "access",
        "dimension": "relational", "negated": True,
        "quantification": "existential"}
    claim, = produce(sentence)
    assert claim["relation"] == "predication"
    assert claim["coordinates"]["polarity"] == "negative"


def test_shall_be_stays_a_copula():
    # the longer copula "shall be" beats the modal "shall" at the same offset
    f = lower("The controller shall be liable.")
    assert (f["subject"], f["predicate"], f["object"]) == ("controller", "shall be", "liable")


def test_is_followed_by_stays_an_ordering():
    # the ordering "is followed by" beats the copula "is" at the same offset
    f = lower("The review is followed by a decision.")
    assert (f["subject"], f["predicate"], f["object"], f["dimension"]) == (
        "review", "is followed by", "decision", "temporal")
    claim, = produce("The review is followed by a decision.")
    assert claim["relation"] == "precedes"


@pytest.mark.parametrize("sentence", [
    "The canopy is green.",          # 'can' inside a word is not the modal
    "The cannon is loaded.",
])
def test_can_inside_a_word_is_not_a_modal(sentence):
    f = lower(sentence)
    assert f["predicate"] == "is"


def test_no_cue_is_none():
    assert lower("Every controller keeps a record.") is None


# --- docs match the grammar (G1) -----------------------------------------------

_ROOT = Path(__file__).resolve().parents[1]
_CARDS = [_ROOT / "docs" / "language-card.md", _ROOT / "skills" / "factual" / "SKILL.md"]


@pytest.mark.parametrize("card", _CARDS, ids=lambda p: p.parent.name)
def test_language_card_documents_every_cue_class(card):
    text = card.read_text("utf-8")
    for key in ("predicate_cues.copula", "predicate_cues.relations.is-a",
                "predicate_cues.relations.part-of", "predicate_cues.relations.has-part",
                "ordering_cues", "modal_cues.modal", "modal_cues.temporal_subordinate",
                "complement_cues.clausal_complement"):
        assert f"`{key}`" in text, (card.name, key)
    for stale in ("without a copula", "has no copula", "structural predicate"):
        assert stale not in text, (card.name, stale)
