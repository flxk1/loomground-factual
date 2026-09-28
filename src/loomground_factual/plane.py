# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The factual plane descriptor (Loomground plane descriptor contract v1).

Published through the ``loomground.planes`` entry-point group under the plane id
``factual``. Everything here is DATA derived from this package at call time: the
nD-system document's closed vocabularies come from ``artifacts/extraction.json``,
the relation -> 5D binding from ``artifacts/binding.json`` (its one home), the
version from ``_version``. ``produce`` is pure and deterministic, returns ``[]``
when the sentence carries no fact, and never repairs a value. This package never
imports the versum; the consumer validates.

This module's ``nd_system()`` document (id ``loomground-factual``) is what gets
registered as an nD system on the versum index: a versum host discovers this
plane via the ``loomground.planes`` entry-point (id ``factual``), loads the
descriptor ``plane()`` returns, and registers its ``nd_system`` under that id on
its own nD-system index -- this package never registers itself; it only
publishes the descriptor a host reads.
"""
from __future__ import annotations

import copy
from typing import Any, Optional

from ._version import __version__
from .grammar import _analyse, _content_clause, load_json

__all__ = ["PLANE_ID", "plane", "nd_system", "binding", "produce", "examples"]

PLANE_ID = "factual"
METHOD = "loomground-factual/lower"
#: the content-clause path's own method label: it never asserted the clause
#: (there is nothing in the sentence to have observed it from -- the subject
#: came from ``context``), so it never carries the plain ``lower`` label an
#: asserted fact gets.
METHOD_ACTION_TYPE = "loomground-factual/content_clause"

#: the plane's axes, in claim order; each is bound to the form slot ``fact.<axis>``
AXES = ("subject", "predicate", "object", "polarity", "quantification")
SLOTS = {f"fact.{axis}": axis for axis in AXES}


def binding() -> dict[str, str]:
    """relation -> 5D dimension, read from the plane's single binding file."""
    return dict(load_json("binding.json")["binding"])


def nd_system() -> dict[str, Any]:
    """The factual nD-system document (``versum.nd.NDSystem.from_dict`` shape)."""
    ex = load_json("extraction.json")

    def closed(vocabulary) -> dict[str, Any]:
        return {"value_type": "controlled_identifier", "vocabulary_mode": "closed",
                "vocabulary": list(vocabulary), "cardinality": "one",
                "primitives": ["equal"]}

    def open_(value_type: str) -> dict[str, Any]:
        return {"value_type": value_type, "vocabulary_mode": "open",
                "cardinality": "one", "primitives": ["equal"]}

    return {
        "id": f"loomground-{PLANE_ID}",
        "namespace": PLANE_ID,
        "version": __version__,
        "axes": {
            "subject": open_("entity_reference"),
            "predicate": open_("concept_reference"),
            "object": open_("concept_reference"),
            "polarity": closed(ex["polarity_values"]),
            "quantification": closed(ex["quantifier_cues"]),
        },
        "bindings": [{"form_slot": slot, "allowed_axes": [axis], "required": True}
                     for slot, axis in SLOTS.items()],
        "validation": {"unknown_values": "reject"},
    }


def _resolve_frame(ctx: dict[str, Any]) -> tuple[Optional[str], Optional[list]]:
    """``(bearer, candidates)`` from ``ctx['frame']`` -- a stack of frame
    dicts, outermost first, ``ctx['frame'][-1]`` the frame enclosing this
    sentence. Both ``None`` when ``ctx`` carries no usable ``'frame'`` (a
    missing key, a non-list, an empty list, or a top frame that is not a
    dict) -- the legacy ``ctx['subject']`` shorthand is read by ``produce``
    itself, not here."""
    frame_stack = ctx.get("frame")
    if isinstance(frame_stack, list) and frame_stack:
        top = frame_stack[-1]
        if isinstance(top, dict):
            bearer = top.get("bearer")
            bearer = bearer if isinstance(bearer, str) and bearer else None
            candidates = top.get("candidates")
            candidates = candidates if isinstance(candidates, list) else None
            return bearer, candidates
    return None, None


def produce(sentence: str, context: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
    """The factual claims in ``sentence`` (at most one), or ``[]``.

    ``context`` is accepted for the contract and, for every sentence this
    plane already lowers on its own (a copula, ordering or modal sentence, or
    a clausal complement), ignored: the factual reading of those depends on
    the sentence alone, and their outputs -- including every published
    example -- are unaffected by whatever ``context`` carries. A temporal
    ordering is published in its canonical direction ("X follows Y" -> Y
    precedes X). Every produced claim carries a ``bearer`` key --
    ``{"local": ..., "inherited": ...}``, exactly one of the two ever
    non-``None`` -- see the "Bearer resolution" section below.

    Bearer resolution -- ``context['frame']`` and ``context['registry']``
    -----------------------------------------------------------------------
    ``context`` may carry two more, both optional, both additive (neither
    changes this function's signature or any pre-existing output key):

    ``context['frame']`` -- a FRAME STACK: a list of frame dicts, outermost
    first, ``context['frame'][-1]`` being the frame enclosing this sentence.
    A frame dict is ``{"bearer": <str or None>, "candidates": <list[str] or
    None>}``. ``frame[-1]['bearer']`` is this sentence's inherited bearer --
    it supersedes the older, single-frame ``context['subject']`` shorthand
    when both are given, and ``context['subject']`` alone still works exactly
    as before this round (an implicit one-frame stack). ``frame[-1]
    ['candidates']`` is the frame's list of prior-mentioned entities, used
    only to judge whether an own-PRONOUN subject is ambiguous (see below).

    ``context['registry']`` -- the document's defined-terms registry, built
    once per document by ``build_registry`` (``loomground_factual.
    build_registry`` / ``registry.build_registry``) from that document's own
    'X means ...', quoted '"X": ...' and 'hereinafter (referred to as) "X"'
    definitions. Supplying it lets a determiner-led common-noun subject that
    would otherwise abstain ("the controller") resolve instead, case
    -insensitively, to its registry entry.

    Supplying EITHER key switches this function into frame-aware mode for
    the one case ``context`` ever changes (below): a bare content clause with
    no bearer available at all -- no own subject, no registry rescue, and an
    empty/falsy inherited bearer -- abstains with the typed reason
    ``NO_BEARER`` instead of silently falling through as ``[]``. Omitting
    both keys (the legacy shape: no ``context``, or ``context`` with at most
    a ``'subject'`` key) reproduces this function's exact pre-existing
    behaviour, byte for byte, including the plain ``[]`` for a bearer-less
    bare clause and for any clause whose out-of-band subject is a truthy
    string, regardless of how "thin" its object is (a single, bare,
    lower-case word such as "authorities" in "Notify authorities." lowers
    exactly as it always did on that path). ``NO_BEARER`` only ever fires on
    an actual clause with no bearer of any kind: a confirmed bare verb
    followed by a GENUINE object (a multi-word span, a capitalised
    /proper-noun-like span, or a determiner-/quantifier-led span -- never a
    single bare lower-case common word); with no subject at all on hand, that
    shape test is the only way to tell a real bearer-less content clause from
    a non-clause fragment ("Hello world.", "12345."), so it gates this
    decision alone. ``AMBIGUOUS_PRONOUN`` fires on a confirmed bare verb with
    a non-empty object -- the pronoun subject is already unambiguous in
    shape, so the fuller GENUINE-object test does not gate it -- but not on a
    lone pronoun with nothing following it at all (e.g. "It."), which returns
    the plain ``[]`` instead, never a typed abstention.

    Three subject shapes and their ``bearer`` output, on the content-clause
    path (an imperative/infinitive clause with no cue of its own -- see
    below): an IMPERATIVE with no subject of its own ("Notify Commission.",
    "Inform Data Subjects of the breach.") INHERITS the enclosing frame's
    bearer -- ``bearer["inherited"]`` is that bearer, ``bearer["local"]`` is
    ``None``. A PRONOUN ("they", "it", "he", "she", "we") or a REGISTRY term
    keeps ITS OWN subject -- ``bearer["local"]`` is that subject,
    ``bearer["inherited"]`` is ``None`` -- unless the pronoun is AMBIGUOUS
    (``context['frame'][-1]['candidates']`` lists more than one distinct
    candidate) or the registry term is SHADOWED (defined twice in the
    document with a different meaning), in which case this function abstains
    with the typed reason ``AMBIGUOUS_PRONOUN`` / ``DEFINITION_SHADOWED``
    instead of guessing. A DETERMINER-LED common-noun subject ("The
    controller", "the controller", "THE CONTROLLER") resolves IDENTICALLY
    regardless of case when it matches a registry term -- to that term's
    lower-cased canonical form, so all three variants above produce the
    identical ``bearer["local"]`` -- and abstains, unchanged from before this
    round, when no registry term matches it (``registry`` unset, or no
    term's head matches the NP). An asserted claim (this plane's own copula,
    ordering, modal or clausal-complement reading, never the content-clause
    path) always carries ``bearer["local"]`` equal to its own ``coordinates
    ["subject"]`` and ``bearer["inherited"]`` ``None``: its subject was
    always read off the sentence itself, never out of band.

    An abstention with a typed reason -- ``AMBIGUOUS_PRONOUN``,
    ``DEFINITION_SHADOWED`` or ``NO_BEARER`` -- is reported as a single
    -element list, ``[{"abstained": True, "reason": <code>, "span": [s0,
    s1]}]``, never a claim dict (no ``coordinates``/``relation``/``method``):
    a consumer distinguishes "no fact" (``[]``) from "abstained for a named
    reason" (this one-element list) by checking for the ``"abstained"`` key.

    The one case ``context`` changes: a norm's content clause, an
    infinitive/bare-verb clause with no subject of its own (e.g. "make a
    solely automated decision on a credit application"), lowered with a
    subject supplied out of band. Set ``context['subject']`` to a non-empty
    string -- the norm's bearer (versum sets it from the parent norm's bearer)
    -- and a cue-free clause lowers with that subject, the clause's leading
    bare verb as predicate, and the rest of the clause (leading-determiner
    stripped, same as every other clause kind) as object. The relation is
    always "predication", so the dimension is always the plane's default
    relation binding: RELATIONAL (``binding.json``'s one entry for any
    predicate that is not is-a/part-of/has-part or a temporal ordering).

    This path activates when EITHER ``context['subject']`` is supplied as a
    non-empty string OR ``context['frame'][-1]['bearer']`` is a non-empty
    string (a frame bearer alone, with no ``'subject'`` key at all, is
    enough -- see "Bearer resolution" above; when both are given, the frame
    bearer supersedes the legacy shorthand). A missing ``context``, an empty
    dict, or a ``context`` whose only relevant keys are all missing/falsy
    leaves the sentence exactly as before (``[]`` for a clause with no cue of
    its own, unchanged for one that already lowers). It never widens the
    three ``lower() -> None`` paths named in
    ``grammar.lower``'s docstring, since it only ever runs after those paths'
    own sentences have already produced ``None`` there too, and it only fires
    on a clause that carries none of the grammar's own cues -- so it can never
    override or silently repair a wrong or missing subject with the clause's
    own (there is none) or a default one. A clause that opens with its own
    subject (once any leading "not"/"never" is stripped) is never forced
    through this path with the context subject spliced on: when that own
    subject is unambiguous -- a closed pronoun ("they", "it", "he", "she",
    "we") or an exactly-two-word Title-Case named subject whose first word is
    not itself a determiner (e.g. "Member States") -- ``_content_clause``
    lowers the clause with that subject instead of the context one; when it
    is a determiner-led common-noun subject ("the reviewer", "the court")
    with no cue-free way to split it from its verb, ``_content_clause``
    abstains (``None``) instead (see its own docstring). Sentence-initial
    capitalisation alone is never enough to read a named subject: a clause's
    first word is capitalised whenever it opens a sentence, proper noun or
    not, so a THREE-OR-MORE-word leading Title-Case run ("Notify Member
    States without delay") is read as a sentence-initial capitalised
    imperative VERB in front of a genuine two-word name -- the context
    subject is kept, and the verb becomes the predicate, exactly as if the
    clause had opened in lower case -- and a leading Title-Case run whose
    first word is itself a determiner ("The Court orders otherwise") is read
    as the same determiner-led common-noun subject as its lower-case form and
    abstains the same way ("the court orders otherwise" and "The Court
    orders otherwise" produce the identical result).

    A claim produced on this path is an ACTION TYPE, not an asserted fact: the
    sentence never asserted it (there is nothing in the clause itself to have
    observed a fact from -- the subject came from ``context``, out of band).
    Such a claim carries ``asserted: False``, ``entry_kind: "action_type"``,
    and ``method: "loomground-factual/content_clause"`` (``METHOD_ACTION_TYPE``)
    -- never the plain ``"loomground-factual/lower"`` label an asserted fact
    gets. Its ``coordinates["polarity"]`` still records the clause's own
    polarity (negative when the clause opens with "not"/"never", or its object
    carries the plane's own negation/empty-quantifier cues); this is the
    action type's own polarity, kept for reference. It is not the ought-side
    authority on whether the parent norm is negated -- that authority is the
    deontic norm's own ``negation`` axis (``loomground-deontic``); a consumer
    reads the norm's ``negation`` for the norm's polarity and this claim's
    ``polarity`` only for the action type's own.

    The relation an action-type claim carries is always ``predication``
    (dimension RELATIONAL, ``binding.json``'s default): it comes from the
    content clause's own relations only, by construction (a content clause
    supplies no is-a/part-of/has-part/ordering cue of its own), never from
    whatever relation or dimension the parent norm happens to carry."""
    ctx = context if isinstance(context, dict) else {}
    frame_bearer, candidates = _resolve_frame(ctx)
    legacy_subject = ctx.get("subject") if ctx.get("subject") else None
    # ``frame[-1]['bearer']`` supersedes the legacy ``context['subject']``
    # shorthand when both are given -- see ``produce``'s "Bearer resolution"
    # docstring section.
    subject_ctx = frame_bearer if frame_bearer else legacy_subject
    registry = ctx.get("registry") if isinstance(ctx.get("registry"), dict) else None
    frame_aware = isinstance(ctx.get("frame"), list) or registry is not None

    rec = _analyse(sentence)
    is_action_type = False
    bearer_local: Optional[str] = None
    bearer_inherited: Optional[str] = None
    if rec is None:
        outcome = None
        if frame_aware:
            outcome = _content_clause(sentence, subject_ctx or "", candidates=candidates,
                                       registry=registry)
        elif subject_ctx:
            outcome = _content_clause(sentence, subject_ctx)
        if isinstance(outcome, dict) and "abstain_reason" in outcome:
            return [{"abstained": True, "reason": outcome["abstain_reason"],
                     "span": list(outcome["span"])}]
        rec = outcome
        is_action_type = rec is not None
        if is_action_type:
            bearer_local = rec.get("bearer_local")
            bearer_inherited = rec.get("bearer_inherited")
    if rec is None:
        return []
    bind = binding()
    polarity = {negated: name for name, negated in
                load_json("extraction.json")["polarity_values"].items()}
    fact = rec["fact"]
    subject, predicate, obj = fact["subject"], fact["predicate"], fact["object"]
    relation = rec["relation"]
    if rec["canonical"] is not None:
        relation, converse = rec["canonical"]
        predicate = relation
        if converse:
            subject, obj = obj, subject
    if not is_action_type:
        # an asserted claim's subject always came from the sentence itself,
        # never out of band -- always its own, never inherited.
        bearer_local, bearer_inherited = subject, None
    claim: dict[str, Any] = {
        "relation": relation,
        "span": list(rec["span"]),
        "coordinates": {
            "subject": subject,
            "predicate": predicate,
            "object": obj,
            "polarity": polarity[fact["negated"]],
            "quantification": fact["quantification"],
        },
        "slots": dict(SLOTS),
        "method": METHOD_ACTION_TYPE if is_action_type else METHOD,
        "bearer": {"local": bearer_local, "inherited": bearer_inherited},
    }
    if is_action_type:
        # an action type, not an asserted fact (rule: the content-clause path
        # never claims a sentence asserted it -- the subject came from
        # context, out of band). See ``produce``'s docstring.
        claim["asserted"] = False
        claim["entry_kind"] = "action_type"
    if rec["subordinate"] is not None:
        name, s0, s1 = rec["subordinate"]
        claim["links"] = [{"type": bind[name], "relation": name, "to_span": [s0, s1]}]
    return [claim]


def examples() -> list[dict[str, Any]]:
    """The plane's published conformance vectors: ``{sentence, expected}``."""
    return copy.deepcopy(load_json("examples.json")["examples"])


def plane() -> dict[str, Any]:
    """Zero-arg entry-point target: the factual plane descriptor."""
    return {
        "plane": PLANE_ID,
        "language_version": __version__,
        "nd_system": nd_system(),
        "binding": binding(),
        "produce": produce,
        "examples": examples(),
    }
