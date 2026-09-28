# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Pin the three ``lower() -> None`` paths named in ``lower``'s docstring:

1. no copula, ordering or modal cue fires at all;
2. a modal cue fires but no verb token follows it (``grammar.py`` ~151);
3. the extracted subject or object is empty (``grammar.py`` ~167).

These three literal sentences are the contract's regression pins, not a claim
that each sentence exercises a distinct path in the current implementation
(``lower('The controller is.')`` and ``lower('Must comply.')`` both end up at
the empty-subject-or-object check; ``lower('The provider cannot.')`` finds no
cue at all, since ``cannot`` at end-of-sentence fails the modal cue's own
trailing lookahead for a following letter). What matters is that all three
return ``None``, as the docs promise.
"""
from loomground_factual import lower


def test_copula_with_empty_object_is_none():
    assert lower("The controller is.") is None


def test_no_cue_fires_is_none():
    assert lower("The provider cannot.") is None


def test_modal_with_empty_subject_and_object_is_none():
    assert lower("Must comply.") is None
