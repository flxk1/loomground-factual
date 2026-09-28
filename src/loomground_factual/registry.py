# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""A document's own defined-terms registry: 'X means ...', a quoted '"X": ...'
definition, and a 'hereinafter (referred to as) "X"' rename, each read off the
raw document text with a plain regex, standard library only, deterministic.

This module never touches a single sentence's factual reading -- it is called
once per document, up front, and its output is handed to ``plane.produce()``
through ``context['registry']`` (see ``plane.produce``'s docstring): a
determiner-led common-noun subject that ``grammar._content_clause`` would
otherwise abstain on ("the controller", case-insensitively) resolves to its
registry entry instead, when the document actually defines that term.

Three sentence shapes populate the registry, tried in this order (first match
per sentence -- a sentence defines at most one term):

1. a quoted term with a colon or dash lead-in: ``"Controller": the natural or
   legal person which ... determines the purposes ... of processing.``
2. a parenthetical rename: ``... determines the purposes of processing
   (hereinafter referred to as the "Controller").`` -- the meaning is
   whatever text precedes the parenthetical in the same sentence.
3. a plain, unquoted 'X means ...': ``Controller means the natural or legal
   person who determines the purposes of processing.``

A term is looked up case-insensitively (``"Controller"``, ``"controller"`` and
``"CONTROLLER"`` all key the same entry) and, for the plain and quoted
patterns, with a leading "the/a/an" stripped ("the Controller" and
"Controller" key the same entry too).

A term defined more than once in the same document, with a DIFFERENT meaning
(compared after whitespace normalisation), is SHADOWED: ``entry["shadowed"]``
is ``True``. A shadowed entry is deliberately kept, not dropped -- a consumer
that resolves a subject through it (``grammar._content_clause``) abstains
with the typed reason ``DEFINITION_SHADOWED`` rather than pick one of the
two meanings.

The registry never repairs or infers a definition the document does not
carry, and it never reads outside the document text handed to it.
"""
from __future__ import annotations

import re
from typing import Any, Optional

__all__ = ["build_registry"]

# one document, split into its own sentences on a sentence-ending '.' or ';'
# followed by whitespace; a plain, deterministic split -- no NLP.
_SENT_SPLIT = re.compile(r"(?<=[.;])\s+")

# 1. a quoted term with a colon/dash lead-in: '"Controller": the natural ...'
_QUOTED = re.compile(r'^\s*"([^"]+)"\s*[:\-–—]\s*(.+?)[.;]?\s*$')

# 2. a parenthetical rename: '... processing (hereinafter referred to as the
# "Controller")'. Group 1 is the meaning (everything before the parenthetical
# in the same sentence); group 2 is the renamed term.
_HEREINAFTER = re.compile(
    r'^(.*?)\(\s*hereinafter\s+(?:referred to as\s+)?(?:the\s+)?"?'
    r"([A-Za-z][A-Za-z \-]*?)\"?\s*\)",
    re.I,
)

# 3. a plain, unquoted 'X means ...' / 'X shall mean ...'.
_MEANS = re.compile(r"^\s*([A-Za-z][A-Za-z \-]*?)\s+(?:means|shall mean)\s+(.+?)[.;]?\s*$", re.I)

_LEADING_ARTICLE = re.compile(r"^(?:the|a|an)\s+", re.I)


def _split_sentences(document_text: str) -> list[str]:
    text = (document_text or "").strip()
    if not text:
        return []
    return [p.strip() for p in _SENT_SPLIT.split(text) if p.strip()]


def _norm_term(term_raw: str) -> str:
    t = re.sub(r"\s+", " ", (term_raw or "")).strip().strip('"').strip()
    t = _LEADING_ARTICLE.sub("", t)
    return t.lower()


def _norm_meaning(meaning_raw: str) -> str:
    return re.sub(r"\s+", " ", (meaning_raw or "")).strip().rstrip(".;").strip()


def _match_definition(sentence: str) -> Optional[tuple[str, str, str]]:
    """``(term_raw, meaning_raw, pattern_name)`` for the first pattern (in the
    module docstring's order) that fires on ``sentence``, or ``None``."""
    m = _QUOTED.match(sentence)
    if m:
        return m.group(1), m.group(2), "quoted"
    m = _HEREINAFTER.search(sentence)
    if m:
        return m.group(2), m.group(1), "hereinafter"
    m = _MEANS.match(sentence)
    if m:
        return m.group(1), m.group(2), "means"
    return None


def build_registry(document_text: str) -> dict[str, dict[str, Any]]:
    """The document's defined-terms registry: ``{term_lower: entry}``.

    Each ``entry`` is ``{"term": <first-seen surface form>, "meaning": <first
    meaning, whitespace-normalised>, "shadowed": <bool>, "definitions": [...]}``
    -- ``definitions`` lists every ``{"meaning", "pattern"}`` hit for that
    term, in document order, so a consumer can inspect what shadowed it.

    Returns ``{}`` for an empty or non-string ``document_text``, or one with
    no definitional sentence at all. Never raises on malformed input."""
    registry: dict[str, dict[str, Any]] = {}
    if not isinstance(document_text, str):
        return registry
    for sentence in _split_sentences(document_text):
        hit = _match_definition(sentence)
        if hit is None:
            continue
        term_raw, meaning_raw, pattern = hit
        term_lower = _norm_term(term_raw)
        meaning = _norm_meaning(meaning_raw)
        if not term_lower or not meaning:
            continue
        entry = registry.get(term_lower)
        if entry is None:
            registry[term_lower] = {
                "term": term_raw.strip(),
                "meaning": meaning,
                "shadowed": False,
                "definitions": [{"meaning": meaning, "pattern": pattern}],
            }
        else:
            entry["definitions"].append({"meaning": meaning, "pattern": pattern})
            if meaning != entry["meaning"]:
                entry["shadowed"] = True
    return registry
