# Changelog

## Unreleased

### Features

* a per-document defined-terms registry, `build_registry(document_text)`
  (`loomground_factual.build_registry`, also `registry.build_registry`),
  built from three sentence shapes: a quoted, colon/dash-led `"X": ...`
  definition; a parenthetical `... (hereinafter referred to as the "X")`
  rename; and a plain, unquoted `X means ...`. A term is keyed
  case-insensitively, with a leading article stripped. A term defined twice
  in the same document with a DIFFERENT meaning is marked `shadowed: True`.
* a frame stack, `context['frame']` (a list of `{"bearer", "candidates"}`
  dicts, innermost last), and the registry above (`context['registry']`),
  both consumed by `plane.produce()`, both optional and additive: `produce`'s
  signature and every pre-existing output key are unchanged, and omitting
  both keys reproduces the pre-existing behaviour byte for byte.
* every claim `produce()` returns now carries a `bearer` key,
  `{"local": ..., "inherited": ...}` (exactly one of the two ever
  non-`None`): an imperative with no subject of its own (e.g. "Notify
  Commission.", "Inform Data Subjects of the breach.") INHERITS the
  enclosing frame's bearer; a pronoun, a named subject, or a registry
  -rescued determiner-led common-noun subject (e.g. "the controller", when
  the registry defines `controller`) keeps its OWN subject. A
  determiner-led subject resolves identically regardless of case ("The
  controller" / "the controller" / "THE CONTROLLER").
* three situations now abstain with a TYPED reason, as a one-element list
  `[{"abstained": True, "reason": ..., "span": [...]}]`, instead of
  guessing: `AMBIGUOUS_PRONOUN` (a pronoun subject with more than one
  distinct candidate antecedent in the enclosing frame); `DEFINITION_SHADOWED`
  (a determiner-led subject resolves to a registry term defined twice with a
  different meaning); `NO_BEARER` (frame-aware mode, a bare content clause,
  and no bearer of any kind available).
* the `examples.json` conformance vectors were regenerated from the current
  `produce()` to include the new `bearer` key on every published claim
  (`tests/test_plane.py::test_round_trip_published_examples`'s exact
  field-for-field equality now includes it).

### Fixes

* L126: `grammar._content_clause`'s "genuine object" shape test (multi-word,
  capitalised, or determiner-/quantifier-led) now gates only the `NO_BEARER`
  decision, never the `AMBIGUOUS_PRONOUN` decision or the ordinary
  `context['subject']`/inherited-frame-bearer path — a prior widening of that
  gate had silently turned every single-lower-case-word-object legacy clause
  ("Notify authorities.", "Delete data.", "Notify users.", "Inform
  recipients.") into `[]`. Regression test: `tests/test_legacy_shape_differential.py`.

* `grammar._content_clause`'s two-word own-NAMED subject candidate is now
  only accepted when a verb actually follows it: "Member States ensure
  compliance ..." still reads "Member States" as the subject, but "Notify
  Commission." — nothing but a sentence terminator follows the two-word run
  "Notify Commission" — now falls through to the ordinary bare-verb reading
  ("Notify" the predicate, "Commission" the object, the enclosing bearer
  inherited), the same way the pre-existing three-or-more-word case does.
  Regression tests: `tests/test_bearer_resolution.py::test_notify_commission_inherits_frame_bearer`.

* `grammar._content_clause`'s own-subject detection no longer mistakes a
  sentence-initial capitalised imperative verb for a named subject. A
  three-or-more-word leading Title-Case run (e.g. "Notify Member States
  without delay", "Inform Data Subjects of the breach") is now read as a
  sentence-initial capitalised verb in front of a genuine two-word name, not
  as a name of its own: the context subject is kept and the verb becomes the
  predicate. A leading Title-Case run whose first word is itself a
  determiner/quantifier (e.g. "The Court orders otherwise") no longer fires
  as a named subject either: it now abstains exactly like its lower-case
  form ("the court orders otherwise"), so capitalisation never flips a
  determiner-led abstention. Genuine own subjects — a closed pronoun
  ("they", "it", "he", "she", "we") and an exactly-two-word Title-Case name
  not led by a determiner (e.g. "Member States") — are unaffected.
  Regression tests: `tests/test_capitalised_imperative_subject.py` (all
  nine cases, including
  `test_capitalised_and_lowercase_court_variants_produce_the_identical_result`
  and `test_capitalised_and_lowercase_court_variants_helper_produce_the_identical_result`);
  pre-existing coverage in `tests/test_content_clause_own_subject.py` and
  `tests/test_content_clause_action_type.py` continues to pass unchanged.

* `plane.produce()`'s subject-vs-frame precedence now matches its own
  docstring and the language card: `context['frame'][-1]['bearer']`
  supersedes the legacy `context['subject']` shorthand when both are given,
  instead of the other way around. Regression test:
  `tests/test_phase1_findings.py::test_frame_bearer_supersedes_legacy_subject_when_both_given`.

* `docs/language-card.md`'s content-clause activation wording no longer
  contradicts the code: a frame bearer alone (`context['frame'][-1]['bearer']`,
  with no `'subject'` key at all) activates the content-clause path, not
  only `context['subject']`. Regression test:
  `tests/test_phase1_findings.py::test_frame_bearer_alone_with_no_subject_key_activates_content_clause`
  and `::test_language_card_no_longer_claims_subject_key_is_required_to_activate`.

* `grammar._content_clause`'s `NO_BEARER` and `AMBIGUOUS_PRONOUN` typed
  abstentions no longer fire on a fragment that is not an actual clause: the
  verb and object checks now run first; for `NO_BEARER` only (see L126
  above), a bare-verb reading's object must also be GENUINE (multi-word,
  capitalised/proper-noun-like, or determiner-/quantifier-led — never a
  single bare lower-case common word). `"Hello world."` and
  `"12345."` (frame bearer `None`) now return `[]`, not `NO_BEARER`; `"It."`
  with more than one candidate antecedent now returns `[]`, not
  `AMBIGUOUS_PRONOUN` (there is no verb after "It"). Regression tests:
  `tests/test_phase1_findings.py::test_no_bearer_never_fires_on_a_non_clause_greeting`,
  `::test_no_bearer_never_fires_on_a_bare_number`,
  `::test_ambiguous_pronoun_never_fires_on_a_pronoun_with_no_verb`.

## 0.1.0 (2026-08-07)


### Features

* initial public release of the loomground-factual plane — the assertoric substrate that lowers free-text assertions into the fixed 5D edge representation.
