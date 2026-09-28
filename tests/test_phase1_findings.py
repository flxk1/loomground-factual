# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Regression pins for the three defects the phase-1 verifier found against
commit 9570c81 (see the ``## factual`` section of the phase-1 findings):

1. ``frame[-1]['bearer']`` must supersede the legacy ``context['subject']``
   shorthand when both are given, matching ``produce``'s own docstring and
   ``docs/language-card.md``.
2. A frame bearer alone (no ``context['subject']`` key at all) must activate
   the content-clause path, not leave the clause at ``[]``.
3. ``NO_BEARER`` and ``AMBIGUOUS_PRONOUN`` must only ever fire on an actual
   verb/object clause: a non-clause fragment ("Hello world.", "12345.",
   "It." with no verb following the pronoun) returns ``[]``, never a typed
   abstention.

Each test below is written to fail against 9570c81's ``plane.py``/
``grammar.py`` behaviour (see the inline note on each).
"""
from __future__ import annotations

from pathlib import Path

from loomground_factual.plane import produce

_CARD = Path(__file__).resolve().parents[1] / "docs" / "language-card.md"

# --- (a) frame bearer supersedes the legacy context['subject'] shorthand ----


def test_frame_bearer_supersedes_legacy_subject_when_both_given():
    # 9570c81: `context.get("subject")` was read first, so this returned
    # `bearer == {"local": None, "inherited": "old"}` -- the frame bearer
    # "new" was silently discarded even though it is documented to win.
    claims = produce("Notify Commission.",
                      {"subject": "old", "frame": [{"bearer": "new", "candidates": None}]})
    assert len(claims) == 1, claims
    assert claims[0]["bearer"] == {"local": None, "inherited": "new"}
    assert claims[0]["coordinates"]["subject"] == "new"


# --- (b) a frame bearer alone (no 'subject' key) activates the clause ------


def test_frame_bearer_alone_with_no_subject_key_activates_content_clause():
    # 9570c81's card (docs/language-card.md ~line 92) still said this path
    # activates "only" on a non-empty context['subject'] string, and left a
    # frame-only context producing `[]`. The code already inherited the
    # frame bearer at 9570c81 for FRAME_CONTROLLER-shaped contexts; this
    # pins that a frame bearer with no 'subject' key at all does the same,
    # and documents it accurately (see docs/language-card.md).
    ctx = {"frame": [{"bearer": "controller", "candidates": None}]}
    assert "subject" not in ctx
    claims = produce("Notify Commission.", ctx)
    assert len(claims) == 1, claims
    assert claims[0]["bearer"] == {"local": None, "inherited": "controller"}
    assert claims[0]["asserted"] is False
    assert claims[0]["entry_kind"] == "action_type"


def test_language_card_no_longer_claims_subject_key_is_required_to_activate():
    # 9570c81's card (docs/language-card.md, then line 92) said this path
    # "activates *only*" on a non-empty context['subject'] string -- stale
    # once a frame bearer alone was documented (and already coded) to
    # activate it too; the outdated claim must be gone from the card.
    card = _CARD.read_text(encoding="utf-8")
    assert "activates *only* when `context['subject']`" not in card
    assert "context['frame'][-1]['bearer']" in card.split(
        "## Content clauses")[1].split("## Subject resolution")[0]


# --- (c) NO_BEARER / AMBIGUOUS_PRONOUN only fire on an actual clause -------


def test_no_bearer_never_fires_on_a_non_clause_greeting():
    # 9570c81: the NO_BEARER check ran before any verb/object check, so this
    # returned `[{"abstained": True, "reason": "NO_BEARER", ...}]`.
    assert produce("Hello world.", {"frame": [{"bearer": None}]}) == []


def test_no_bearer_never_fires_on_a_bare_number():
    # 9570c81: same bug -- "12345." has no verb token at all, but NO_BEARER
    # still fired before the verb check ever ran.
    assert produce("12345.", {"frame": [{"bearer": None}]}) == []


def test_ambiguous_pronoun_never_fires_on_a_pronoun_with_no_verb():
    # 9570c81: AMBIGUOUS_PRONOUN was decided as soon as the pronoun was seen,
    # before checking whether any verb follows it -- "It." has none.
    ctx = {"frame": [{"bearer": "controller", "candidates": ["controller", "processor"]}]}
    assert produce("It.", ctx) == []


def test_no_bearer_still_fires_on_a_genuine_bare_clause():
    # unaffected by the fix: a real bare-verb clause with no bearer at all
    # still abstains typed, not silently as [].
    result = produce("examine every rejection", {"frame": [{"bearer": None}]})
    assert result == [{"abstained": True, "reason": "NO_BEARER", "span": result[0]["span"]}]


def test_ambiguous_pronoun_still_fires_on_a_genuine_pronoun_clause():
    # unaffected by the fix: a real pronoun clause with >1 candidate still
    # abstains typed.
    ctx = {"frame": [{"bearer": "controller", "candidates": ["controller", "processor"]}]}
    result = produce("they notify the data subject without delay", ctx)
    assert result == [{"abstained": True, "reason": "AMBIGUOUS_PRONOUN",
                       "span": result[0]["span"]}]
