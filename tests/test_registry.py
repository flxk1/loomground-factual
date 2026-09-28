# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Per-document defined-terms registry (``registry.build_registry``): each of
the three definition patterns populates the registry; a term defined twice
with a different meaning is SHADOWED; a term defined twice with the SAME
meaning (after whitespace normalisation) is not."""
from __future__ import annotations

from loomground_factual import build_registry
from loomground_factual.registry import build_registry as build_registry_direct


def test_reexported_from_package_root():
    assert build_registry is build_registry_direct


# --- each of the three patterns populates the registry ----------------------

def test_plain_means_pattern_populates_registry():
    doc = "Controller means the natural or legal person who determines the purposes of processing."
    reg = build_registry(doc)
    assert "controller" in reg
    assert reg["controller"]["meaning"] == \
        "the natural or legal person who determines the purposes of processing"
    assert reg["controller"]["shadowed"] is False
    assert reg["controller"]["definitions"][0]["pattern"] == "means"


def test_quoted_colon_pattern_populates_registry():
    doc = '"Processor": a natural or legal person which processes personal data on behalf of the controller.'
    reg = build_registry(doc)
    assert "processor" in reg
    assert reg["processor"]["meaning"] == \
        "a natural or legal person which processes personal data on behalf of the controller"
    assert reg["processor"]["definitions"][0]["pattern"] == "quoted"


def test_hereinafter_pattern_populates_registry():
    doc = ('The natural or legal person who determines the purposes of '
           'processing (hereinafter referred to as the "Controller").')
    reg = build_registry(doc)
    assert "controller" in reg
    assert reg["controller"]["meaning"] == \
        "The natural or legal person who determines the purposes of processing"
    assert reg["controller"]["definitions"][0]["pattern"] == "hereinafter"


# --- case-insensitive, article-insensitive keying ----------------------------

def test_term_keyed_case_and_article_insensitively():
    doc = "The Controller means the natural or legal person who determines the purposes of processing."
    reg = build_registry(doc)
    assert "controller" in reg
    assert reg["controller"]["term"] == "The Controller"


# --- shadowing: same term, different meaning, in the same document ----------

def test_same_term_defined_twice_with_different_meaning_is_shadowed():
    doc = (
        "Controller means the natural or legal person who determines the purposes of processing. "
        "Controller means any public authority which processes personal data."
    )
    reg = build_registry(doc)
    assert reg["controller"]["shadowed"] is True
    assert len(reg["controller"]["definitions"]) == 2


def test_same_term_defined_twice_with_the_same_meaning_is_not_shadowed():
    doc = (
        "Controller means the natural or legal person who determines the purposes of processing. "
        "Controller means the natural or legal person who determines the purposes of processing."
    )
    reg = build_registry(doc)
    assert reg["controller"]["shadowed"] is False


# --- no definitional sentence at all -----------------------------------------

def test_no_definitional_sentence_yields_empty_registry():
    assert build_registry("The controller notifies the authority.") == {}
    assert build_registry("") == {}
    assert build_registry(None) == {}  # type: ignore[arg-type]
