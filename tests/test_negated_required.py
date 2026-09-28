# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Pin the current, documented behaviour of "is required to" and its two
negated phrasings, "is not required to" and "is required not to".

Only the plain "is/are required to" (with nothing between "is"/"are" and
"required", and nothing between "required" and "to") is a *modal* cue: the
auxiliary is stripped and the next verb becomes the predicate (see
``artifacts/extraction.json``'s ``modal_cues.modal``). Inserting "not" on
either side of "required" breaks that contiguous match, so the sentence falls
through to the plain *copula* cue ("is"/"are") instead: the copula stays as
the predicate, "required (not) to ..." stays inside the object, and
``negated`` is still ``True`` because the object-side negation scan
(``_NEG.search(obj_raw[:24])``) still finds "not". This is documented, not
fixed, in this contract: the fix would touch ``artifacts/extraction.json``,
which is outside this task's file territory, and patching the regex only in
``grammar.py`` would duplicate cue vocabulary outside the plane's single JSON
source. See README.md, llms.txt, docs/language-card.md and
skills/factual/SKILL.md for the narrowed claim.
"""
from loomground_factual import lower


def test_is_required_to_control_strips_the_auxiliary():
    result = lower("The provider is required to comply with the code.")
    assert result["subject"] == "provider"
    assert result["predicate"] == "comply"
    assert result["object"] == "with the code"
    assert result["negated"] is False


def test_is_not_required_to_leaves_the_copula_in_the_predicate():
    result = lower("The provider is not required to comply with the code.")
    assert result["subject"] == "provider"
    assert result["predicate"] == "is"
    assert result["object"] == "not required to comply with the code"
    assert result["negated"] is True


def test_is_required_not_to_leaves_the_copula_in_the_predicate():
    result = lower("The provider is required not to comply with the code.")
    assert result["subject"] == "provider"
    assert result["predicate"] == "is"
    assert result["object"] == "required not to comply with the code"
    assert result["negated"] is True
