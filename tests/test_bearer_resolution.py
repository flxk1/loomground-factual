# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Subject resolution: ``produce``'s ``bearer`` output key, the frame-stack
``context['frame']`` and the defined-terms ``context['registry']``.

Round covers: an imperative inherits the enclosing frame's bearer
(``bearer.inherited`` set, ``bearer.local`` null); a pronoun with one
candidate antecedent, and a registry-defined term, each keep their own
subject (``bearer.local``); a determiner-led NP resolves identically
regardless of case when the registry defines it; an ambiguous pronoun and a
shadowed definition each abstain with a typed reason code instead of
guessing.
"""
from __future__ import annotations

from loomground_factual import build_registry
from loomground_factual.grammar import _content_clause
from loomground_factual.plane import produce

FRAME_CONTROLLER = {"frame": [{"bearer": "controller", "candidates": ["controller"]}]}


# --- imperatives inherit the enclosing frame's bearer ------------------------

def test_notify_commission_inherits_frame_bearer():
    claims = produce("Notify Commission.", FRAME_CONTROLLER)
    assert len(claims) == 1, claims
    c = claims[0]
    assert c["coordinates"]["subject"] == "controller"
    assert c["coordinates"]["predicate"] == "notify"
    assert "Commission" in c["coordinates"]["object"]
    assert c["bearer"] == {"local": None, "inherited": "controller"}


def test_inform_data_subjects_inherits_frame_bearer():
    claims = produce("Inform Data Subjects of the breach.", FRAME_CONTROLLER)
    assert len(claims) == 1, claims
    c = claims[0]
    assert c["coordinates"]["subject"] == "controller"
    assert c["coordinates"]["predicate"] == "inform"
    assert c["bearer"] == {"local": None, "inherited": "controller"}


def test_legacy_subject_shorthand_also_inherits_and_is_reported_as_inherited():
    claims = produce("examine every rejection", {"subject": "reviewer"})
    assert len(claims) == 1, claims
    assert claims[0]["bearer"] == {"local": None, "inherited": "reviewer"}


# --- a pronoun with one candidate antecedent keeps its own subject ----------

def test_single_candidate_pronoun_keeps_its_own_subject():
    ctx = {"frame": [{"bearer": "controller", "candidates": ["controller"]}]}
    claims = produce("they notify the data subject without delay", ctx)
    assert len(claims) == 1, claims
    c = claims[0]
    assert c["coordinates"]["subject"] == "they"
    assert c["bearer"] == {"local": "they", "inherited": None}


def test_pronoun_with_no_candidates_list_keeps_old_behaviour():
    # no ambiguity check at all when the frame carries no candidates list
    claims = produce("they notify the data subject without delay",
                      {"frame": [{"bearer": "controller"}]})
    assert len(claims) == 1, claims
    assert claims[0]["coordinates"]["subject"] == "they"


# --- a registry-defined term keeps its own subject ---------------------------

REGISTRY_DOC = "Controller means the natural or legal person who determines the purposes of processing."


def test_registry_defined_term_keeps_its_own_subject():
    registry = build_registry(REGISTRY_DOC)
    ctx = {"subject": None, "frame": [{"bearer": None}], "registry": registry}
    claims = produce("the controller notifies the authority", ctx)
    assert len(claims) == 1, claims
    c = claims[0]
    assert c["coordinates"]["subject"] == "controller"
    assert c["coordinates"]["predicate"] == "notifies"
    assert c["bearer"] == {"local": "controller", "inherited": None}


# --- determiner-led NPs resolve identically regardless of case -------------

def test_the_controller_case_variants_produce_the_identical_bearer():
    registry = build_registry(REGISTRY_DOC)
    ctx = {"registry": registry, "frame": [{"bearer": None}]}
    lower = produce("the controller notifies the authority", ctx)
    mixed = produce("The controller notifies the authority", ctx)
    shout = produce("THE CONTROLLER notifies the authority", ctx)
    for claims in (lower, mixed, shout):
        assert len(claims) == 1, claims
        assert claims[0]["coordinates"]["subject"] == "controller"
        assert claims[0]["bearer"]["local"] == "controller"


def test_helper_resolves_case_variants_identically():
    registry = build_registry(REGISTRY_DOC)
    lower = _content_clause("the controller notifies the authority", "", registry=registry)
    upper = _content_clause("THE CONTROLLER notifies the authority", "", registry=registry)
    mixed = _content_clause("The controller notifies the authority", "", registry=registry)
    for rec in (lower, upper, mixed):
        assert rec is not None
        assert rec["fact"]["subject"] == "controller"
        assert rec["bearer_local"] == "controller"


# --- an ambiguous pronoun abstains with a typed reason -----------------------

def test_ambiguous_pronoun_abstains_with_typed_reason():
    ctx = {"frame": [{"bearer": "controller", "candidates": ["controller", "processor"]}]}
    result = produce("they notify the data subject without delay", ctx)
    assert result == [{"abstained": True, "reason": "AMBIGUOUS_PRONOUN",
                       "span": result[0]["span"]}]


def test_ambiguous_pronoun_helper_abstains_with_typed_reason():
    rec = _content_clause("they notify the data subject", "controller",
                           candidates=["controller", "processor"])
    assert rec == {"abstain_reason": "AMBIGUOUS_PRONOUN", "span": rec["span"]}


# --- a shadowed definition abstains with a typed reason ----------------------

SHADOWED_DOC = (
    "Controller means the natural or legal person who determines the purposes of processing. "
    "Controller means any public authority which processes personal data."
)


def test_shadowed_definition_abstains_with_typed_reason():
    registry = build_registry(SHADOWED_DOC)
    assert registry["controller"]["shadowed"] is True
    ctx = {"registry": registry, "frame": [{"bearer": None}]}
    result = produce("the controller notifies the authority", ctx)
    assert result == [{"abstained": True, "reason": "DEFINITION_SHADOWED",
                       "span": result[0]["span"]}]


def test_shadowed_definition_helper_abstains_with_typed_reason():
    registry = build_registry(SHADOWED_DOC)
    rec = _content_clause("the controller notifies the authority", "", registry=registry)
    assert rec == {"abstain_reason": "DEFINITION_SHADOWED", "span": rec["span"]}


# --- no bearer at all abstains with a typed reason (frame-aware mode only) --

def test_no_bearer_at_all_abstains_with_typed_reason_in_frame_aware_mode():
    ctx = {"frame": [{"bearer": None}]}
    result = produce("examine every rejection", ctx)
    assert result == [{"abstained": True, "reason": "NO_BEARER", "span": result[0]["span"]}]


def test_legacy_call_shape_with_no_bearer_still_returns_plain_empty_list():
    # no 'frame'/'registry' key at all: exact pre-existing behaviour, no
    # typed reason -- frame-aware mode is opt-in only.
    assert produce("examine every rejection", {}) == []
    assert produce("examine every rejection") == []


# --- determiner-led NP with no registry match still abstains, unchanged -----

def test_determiner_led_np_with_no_registry_match_still_abstains_plain():
    ctx = {"registry": {}, "frame": [{"bearer": "controller"}]}
    assert produce("the reviewer intervenes", ctx) == []
