# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Differential pin against commit 9570c81's ``produce()`` output, for the
regression ledger L126 fix: the "genuine object" shape test (multi-word,
capitalised, or determiner-/quantifier-led -- see ``grammar._content_clause``'s
own docstring) must gate ONLY the ``NO_BEARER`` decision, never the ordinary
``context['subject']`` / inherited-frame-bearer path, and never the
``AMBIGUOUS_PRONOUN`` decision either (that pronoun subject is already
unambiguous in shape). Before this fix, the gate had been widened to cover
every return path in ``_content_clause``, which silently turned every
single-lower-case-word-object legacy clause -- "Notify authorities.",
"Delete data." and the like -- into ``[]``, a regression from 9570c81's
behaviour on that path.

``tests/fixtures/legacy_shape_9570c81.json`` records ``(sentence, context) ->
produce() output`` for a corpus of short imperative/pronoun clauses, exactly as
commit 9570c81 (via a ``git archive`` export, never a ``git worktree``) produces
them. This test asserts HEAD's ``produce()`` output byte-equals (canonical,
sorted-key JSON) the fixture for every entry, except the two named in
``DOCUMENTED_CHANGES`` below -- both genuine, deliberate divergences from
9570c81, not regressions: 9570c81 itself had the very over-fire bug that a
later round (commit ad91c96, "Fix subject-vs-frame precedence and
typed-abstention scope in produce()") fixed, and this L126 fix does not
reintroduce it.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loomground_factual.plane import produce

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "legacy_shape_9570c81.json"

#: entries where HEAD's ``produce()`` output is EXPECTED to diverge from the
#: 9570c81 fixture value, each with a one-line reason citing the finding that
#: justifies the divergence. Keyed by the input sentence (this corpus never
#: repeats a sentence across two documented-change entries).
DOCUMENTED_CHANGES: dict[str, str] = {
    "Hello world.": (
        "L126: NO_BEARER only fires once a verb AND a genuine object are "
        "confirmed; 9570c81 decided NO_BEARER before checking for a verb at "
        "all, so a non-clause greeting with no bearer wrongly abstained "
        "typed instead of returning the plain [] a non-clause deserves "
        "(the exact defect commit ad91c96 fixed; see "
        "test_phase1_findings.py::test_no_bearer_never_fires_on_a_non_clause_greeting, "
        "not in this round's territory but already pinning this)."
    ),
    "It.": (
        "L126: AMBIGUOUS_PRONOUN only fires once a verb is confirmed to "
        "follow the pronoun; 9570c81 decided ambiguity as soon as the "
        "pronoun was matched, before any verb check, so a lone pronoun with "
        "nothing following it wrongly abstained typed instead of returning "
        "the plain [] a non-clause deserves (the exact defect commit "
        "ad91c96 fixed; see "
        "test_phase1_findings.py::test_ambiguous_pronoun_never_fires_on_a_pronoun_with_no_verb, "
        "not in this round's territory but already pinning this)."
    ),
}

#: the five inputs the contract names explicitly (four legacy-path restorations
#: plus the ambiguous-pronoun abstention that must keep working) -- each gets
#: its own named test below, in addition to the corpus-wide loop.
_LEGACY_RESTORED = [
    ("Notify authorities.", {"subject": "controller"}),
    ("Delete data.", {"subject": "controller"}),
    ("Notify users.", {"subject": "controller"}),
    ("Inform recipients.", {"frame": [{"bearer": "controller"}]}),
]
_AMBIGUOUS_PRONOUN_KEPT = (
    "It notifies authorities.",
    {"frame": [{"bearer": "controller", "candidates": ["controller", "processor"]}]},
)


def _load_fixture() -> list[dict[str, Any]]:
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def test_fixture_has_at_least_thirty_entries():
    entries = _load_fixture()
    assert len(entries) >= 30, len(entries)


def test_fixture_covers_both_context_shapes_and_object_shapes():
    entries = _load_fixture()
    has_legacy_subject = any("subject" in e["context"] for e in entries)
    has_frame_context = any("frame" in e["context"] for e in entries)
    assert has_legacy_subject and has_frame_context

    def obj_of(e: dict[str, Any]) -> str:
        exp = e["expected"]
        if exp and isinstance(exp, list) and "coordinates" in exp[0]:
            return exp[0]["coordinates"]["object"]
        return ""

    objs = [obj_of(e) for e in entries]
    has_single_lower = any(o and len(o.split()) == 1 and o[0].islower() for o in objs)
    has_capitalised = any(o and o[0].isupper() for o in objs)
    has_multiword = any(o and len(o.split()) > 1 for o in objs)
    assert has_single_lower, "corpus must cover a lower-case single-word object"
    assert has_capitalised, "corpus must cover a capitalised-start object"
    assert has_multiword, "corpus must cover a multi-word object"


def test_every_documented_change_has_a_nonempty_reason_citing_a_finding():
    assert DOCUMENTED_CHANGES, "no exceptions declared to justify"
    for sentence, reason in DOCUMENTED_CHANGES.items():
        assert isinstance(reason, str) and reason.strip()
        assert "L1" in reason or "L2" in reason or "L3" in reason, (
            f"reason for {sentence!r} does not cite an L-number finding"
        )


def test_head_matches_fixture_for_every_undocumented_entry():
    entries = _load_fixture()
    mismatches = []
    for entry in entries:
        sentence = entry["sentence"]
        context = entry["context"]
        expected = entry["expected"]
        actual = produce(sentence, context)
        if sentence in DOCUMENTED_CHANGES:
            # a documented, deliberate divergence -- assert it actually
            # DIFFERS (an entry that silently stopped diverging is stale and
            # should be removed from DOCUMENTED_CHANGES, not left here).
            assert _canonical(actual) != _canonical(expected), (
                f"{sentence!r} is in DOCUMENTED_CHANGES but HEAD now matches "
                "the 9570c81 fixture -- remove the stale exception"
            )
            continue
        if _canonical(actual) != _canonical(expected):
            mismatches.append((sentence, context, expected, actual))
    assert not mismatches, mismatches


def test_documented_changes_keys_are_all_present_in_the_fixture():
    entries = _load_fixture()
    sentences = {e["sentence"] for e in entries}
    for sentence in DOCUMENTED_CHANGES:
        assert sentence in sentences, (
            f"DOCUMENTED_CHANGES names {sentence!r}, which is not in the fixture"
        )


# --- the five contract-named inputs, each its own explicit test ------------


def test_notify_authorities_with_legacy_subject_context_restored():
    result = produce("Notify authorities.", {"subject": "controller"})
    assert len(result) == 1, result
    c = result[0]
    assert c["coordinates"]["subject"] == "controller"
    assert c["coordinates"]["predicate"] == "notify"
    assert c["coordinates"]["object"] == "authorities"
    assert c["bearer"] == {"local": None, "inherited": "controller"}
    assert c["asserted"] is False
    assert c["entry_kind"] == "action_type"


def test_delete_data_with_legacy_subject_context_restored():
    result = produce("Delete data.", {"subject": "controller"})
    assert len(result) == 1, result
    c = result[0]
    assert c["coordinates"]["subject"] == "controller"
    assert c["coordinates"]["predicate"] == "delete"
    assert c["coordinates"]["object"] == "data"
    assert c["bearer"] == {"local": None, "inherited": "controller"}


def test_notify_users_with_legacy_subject_context_restored():
    result = produce("Notify users.", {"subject": "controller"})
    assert len(result) == 1, result
    c = result[0]
    assert c["coordinates"]["subject"] == "controller"
    assert c["coordinates"]["predicate"] == "notify"
    assert c["coordinates"]["object"] == "users"
    assert c["bearer"] == {"local": None, "inherited": "controller"}


def test_inform_recipients_with_frame_context_restored():
    result = produce("Inform recipients.", {"frame": [{"bearer": "controller"}]})
    assert len(result) == 1, result
    c = result[0]
    assert c["coordinates"]["subject"] == "controller"
    assert c["coordinates"]["predicate"] == "inform"
    assert c["coordinates"]["object"] == "recipients"
    assert c["bearer"] == {"local": None, "inherited": "controller"}


def test_ambiguous_pronoun_abstention_still_fires_with_thin_object():
    sentence, context = _AMBIGUOUS_PRONOUN_KEPT
    result = produce(sentence, context)
    assert result == [{"abstained": True, "reason": "AMBIGUOUS_PRONOUN",
                       "span": result[0]["span"]}], result


def test_legacy_restored_inputs_all_present_in_corpus_and_undocumented():
    entries = _load_fixture()
    keyed = {(e["sentence"], _canonical(e["context"])) for e in entries}
    for sentence, context in _LEGACY_RESTORED + [_AMBIGUOUS_PRONOUN_KEPT]:
        assert (sentence, _canonical(context)) in keyed, (
            f"{sentence!r} / {context!r} is missing from the fixture corpus"
        )
        assert sentence not in DOCUMENTED_CHANGES, (
            f"{sentence!r} is a contract-restored input; it must not be an "
            "exception"
        )
