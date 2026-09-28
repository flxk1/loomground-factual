# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Factual language: lower a free-text assertion into a fixed-5D edge.

A fact is a relation between entities, so it lowers straight onto the 5D floor.
The relation -> 5D dimension map is DATA in ``artifacts/binding.json`` (is-a,
part-of, has-part -> STRUCTURAL; temporal ordering precedes/follows -> TEMPORAL;
any other predicate, "predication" -> RELATIONAL); polarity and quantification
ride as edge properties. Three sentence shapes lower: a copula ("is", "means",
"consists of" ...), an ordering ("follows", "comes before" ...) and a modal
auxiliary ("must not", "shall", "may", "cannot", "is required to" ...), which is
stripped to the propositional content. A clausal complement ("knows that ...")
is lowered as its own fact with its own sub-span, never as the attitude. When
two cues start at the same offset the longest match wins. ``clean_entity``
is the shared NP-head primitive the modal languages (deontic bearer, epistemic
holder) consume, so the addressee vocabulary lives in one place. Standard library
only; cues are DATA in ``artifacts/extraction.json``.

``lower()`` returns ``None`` on exactly three paths, in this order: (1) no
copula, ordering or modal cue fires anywhere in the (sub-)clause; (2) a modal
cue fires but no verb token follows it; (3) the extracted subject or object is
empty once trimmed. See ``lower``'s own docstring for the exact wording.

A fourth shape, a content clause, lowers only through ``plane.produce()``'s
``context`` parameter, never through ``lower()``: an infinitive/bare-verb
clause with no subject of its own (e.g. "make a solely automated decision on
a credit application" -- the propositional content left once a parent norm's
modal auxiliary and bearer have already been peeled off elsewhere). It has,
by construction, none of this grammar's own cues. Given such a clause and a
subject out of band, ``_content_clause`` fires only when the clause is
genuinely cue-free (so it never intercepts the three ``None`` paths above,
each of which already has a cue), and both a leading bare verb and its
remaining object are present once the clause's subject -- own or contextual
-- is read off. Such a claim is an ACTION TYPE, not an asserted fact --
``plane.produce`` marks it ``asserted: False`` / ``entry_kind: "action_type"``
and gives it its own method label, never the plain "lower" label an
observed/asserted fact gets. A leading "not"/"never" keeps negative polarity
on that action-type output. See ``_content_clause``'s own docstring and
``plane.produce``'s ``context`` parameter for the exact contract.

A clause may carry its OWN subject rather than the out-of-band one: a closed
pronoun ("they", "it", "he", "she", "we") or an exactly-two-word Title-Case
named subject (e.g. "Member States") whose first word is not itself a
determiner/quantifier is read off, verbatim, as that claim's subject -- never
the context subject -- with the predicate starting strictly after it (so the
predicate never begins with or contains the subject token).

Sentence-initial capitalisation is not, on its own, evidence of a named
subject: a clause's first word is capitalised whenever the clause opens a
sentence, whether that word is a proper noun or an ordinary imperative verb
("Notify Member States without delay" opens with the verb "notify", not a
three-word name of its own; "Inform Data Subjects of the breach" likewise
opens with "inform"). So a leading Title-Case run of THREE OR MORE words, and
a leading Title-Case run whose first word is itself a determiner/quantifier
("The Court orders otherwise", capitalised only because it opens the
sentence, not because it names anyone), are never read as a named subject:
both fall through to the ordinary bare-verb / determiner-abstention handling
below, exactly as the same clause would if it opened in lower case. This is
why "The Court orders otherwise" and "the court orders otherwise" take the
identical path and produce the identical result: capitalisation never flips
a determiner-led abstention into a named-subject match.

A determiner-led common-noun subject ("the reviewer", "the court") is also
its own subject, but there is no cue-free way to split such a multi-word
common-noun span from its verb without guessing, so that shape still
abstains (``None``) rather than guess or borrow the context subject --
UNLESS ``plane.produce`` was given the document's defined-terms registry
(``context['registry']``, see ``registry.build_registry``), in which case a
determiner-led subject whose head matches a registry term (case
-insensitively -- "The controller", "the controller" and "THE CONTROLLER"
all resolve identically) is read as that registry term instead of
abstaining; see ``_content_clause``'s own docstring. A clause with none of
these shapes -- no cue-free way to read an own subject off it at all --
keeps inheriting the out-of-band/frame-stack bearer, unchanged (see
``plane.produce``'s ``context['frame']``).

A two-word own-NAMED candidate is only genuinely a subject when a verb
follows it: "Member States ensure compliance ..." has one; "Notify
Commission." does not (nothing but a sentence terminator follows the
two-word run "Notify Commission"), so it falls through to the ordinary
bare-verb reading -- the sentence-initial capitalised imperative VERB
"Notify" in front of a single-word capitalised OBJECT "Commission" -- the
same way the three-plus-word case above does. See ``_content_clause``'s
docstring.

A content clause's resolved subject is reported on its own record as
EITHER its own (``bearer_local``) OR the out-of-band/inherited one
(``bearer_inherited``), never both: an imperative with no subject of its
own inherits (``bearer_inherited`` set, ``bearer_local`` ``None``); a
pronoun, a named subject, or a registry-rescued determiner-led subject
keeps its own (``bearer_local`` set, ``bearer_inherited`` ``None``) --
UNLESS a pronoun is AMBIGUOUS (more than one distinct candidate antecedent
in the enclosing frame, ``context['frame'][-1]['candidates']``) or a
registry term is SHADOWED (the document defines it twice with a different
meaning), in which case ``_content_clause`` abstains with a typed reason
(``AMBIGUOUS_PRONOUN`` / ``DEFINITION_SHADOWED``) instead of guessing. See
``plane.produce``'s ``bearer`` output key and ``registry.build_registry``.

Only the contiguous "is/are required to" is the modal cue's own "required to"
alternative. "is/are ... not ... required to" and "is/are required not to"
break that contiguity, so they do not fire the modal cue at all and fall
through to the plain copula cue ("is"/"are") instead: the copula is *not*
stripped from the predicate for those two negated phrasings, unlike the plain
"is required to" form. ``negated`` still comes out ``True`` for both, because
the copula path's own object-side negation scan (``_NEG`` over the leading
object text) still finds "not".
"""
from __future__ import annotations

import json
import re
from importlib.resources import files
from typing import Any, Optional

__all__ = ["load_json", "clean_entity", "lower", "_content_clause"]


def load_json(name: str) -> Any:
    return json.loads((files("loomground_factual") / "artifacts" / name).read_text("utf-8"))


_EX = load_json("extraction.json")
_BINDING = load_json("binding.json")["binding"]
_PRED = _EX["predicate_cues"]
_COP = re.compile(_PRED["copula"], re.I)
_RELATIONS = [(name, re.compile(p, re.I)) for name, p in _PRED["relations"].items()]
_DEFAULT_RELATION = _PRED["default_relation"]
_ORDERING = [(name, re.compile(c["pattern"], re.I), c["canonical"], bool(c["converse"]))
             for name, c in _EX["ordering_cues"].items()]
_MODAL = re.compile(_EX["modal_cues"]["modal"], re.I)
_SUBORDINATE = [(name, re.compile(p, re.I))
                for name, p in _EX["modal_cues"]["temporal_subordinate"].items()]
_COMPLEMENT = re.compile(_EX["complement_cues"]["clausal_complement"], re.I)
_NEG = re.compile(_EX["polarity_cues"]["negation"], re.I)
_UNIV = re.compile(_EX["quantifier_cues"]["universal"], re.I)
_EMPTY = re.compile(_EX["quantifier_cues"]["empty"], re.I)
_MARKERS = re.compile(_EX["entity_cues"]["entity_markers"], re.I)
_LEAD = re.compile(_EX["entity_cues"]["entity_lead"], re.I)
_TRAIL = re.compile(_EX["entity_cues"]["entity_trail"], re.I)
_OBJ_LEAD = re.compile(r"^(?:not\s+)?(?:a|an|the|one of(?: the)?|part of)\s+", re.I)
_VERB = re.compile(r"\s*([A-Za-z][A-Za-z-]*)")
_TRIM = " .,;:"
# a content clause's own leading negation ("not disclose ...", "never process
# ..."): stripped before verb detection so "not"/"never" is never mistaken for
# the clause's bare verb, and recorded as polarity (see ``_content_clause``).
_LEADING_NEG = re.compile(r"^(?:not|never)\b\s*", re.I)
# a content clause's own PRONOUN subject: a closed, unambiguous set ("they",
# "it", "he", "she", "we") that can never be confused with a bare verb, so it
# is read off directly rather than folded into the predicate (see
# ``_content_clause``'s "own subject" handling).
_OWN_PRONOUN = re.compile(r"^(they|it|he|she|we)\b", re.I)
# a content clause's own NAMED subject CANDIDATE: two or more consecutive
# Title-Case words at the very start of the clause (e.g. "Member States").
# This regex only finds the candidate span; ``_content_clause`` still decides
# whether it is genuinely a named subject, because a clause's FIRST word is
# capitalised whenever the clause opens a sentence -- proper noun or not --
# so sentence-initial capitalisation alone is not evidence of anything.
# ``_content_clause`` only accepts an EXACTLY two-word match whose first word
# is not itself a determiner/quantifier (``_LEAD``) as a named subject: a
# three-plus-word match ("Notify Member States", "Inform Data Subjects") is a
# leading capitalised imperative VERB in front of a genuine two-word name,
# and a match whose first word is a determiner ("The Court") is a
# determiner-led common-noun subject capitalised only by sentence position --
# both fall through to the ordinary bare-verb / determiner-abstention
# handling, exactly as the same clause in all lower case would. A single
# capitalized word is still deliberately NOT enough by itself (this regex
# requires 2+).
_OWN_NAMED = re.compile(r"^[A-Z][A-Za-z'-]*(?:\s+[A-Z][A-Za-z'-]*)+\b")

# candidate kinds. When two cues start at the same offset the LONGEST match wins
# (maximal munch): "is followed by" (ordering) and "is required to" (modal) beat
# the bare copula "is"; "shall be" (copula) beats the modal "shall". The kind
# order only breaks a remaining tie of equal length.
_ORDER_KIND, _COPULA_KIND, _MODAL_KIND = 0, 1, 2


def clean_entity(span: str) -> str:
    """Reduce a span to its addressee/entity NP head: strip list/paragraph markers,
    take the NP after the last comma of a subordinate lead-in, drop a leading
    determiner/quantifier. Shared by deontic (bearer) and epistemic (holder)."""
    s = _MARKERS.sub("", (span or "").strip()).strip()
    if "," in s:
        s = s.rsplit(",", 1)[-1].strip()
    s = _LEAD.sub("", s).strip()
    s = _TRAIL.sub("", s).strip()   # drop a trailing relative/qualifier clause
    return s.strip(" .,;:")


def _trim(text: str, start: int, end: int) -> tuple[int, int]:
    """Narrow ``[start, end)`` past surrounding whitespace and trailing punctuation."""
    while start < end and text[start].isspace():
        start += 1
    while end > start and (text[end - 1].isspace() or text[end - 1] in _TRIM):
        end -= 1
    return start, end


def _quantification(subj_raw: str) -> str:
    if _EMPTY.search(subj_raw):
        return "empty"
    if _UNIV.search(subj_raw):
        return "universal"
    return "existential"


def _candidates(text: str) -> list[tuple[int, int, Any, int]]:
    """Every cue hit as ``(start, kind, hit, length)``, best first: earliest start,
    then longest cue (trailing whitespace excluded), then kind order."""
    out: list[tuple[int, int, Any, int]] = []
    m = _COP.search(text)
    if m:
        out.append((m.start(), _COPULA_KIND, m, len(m.group(0).rstrip())))
    for name, pat, canonical, converse in _ORDERING:
        om = pat.search(text)
        if om:
            out.append((om.start(), _ORDER_KIND, (om, name, canonical, converse),
                        len(om.group(0).rstrip())))
    mm = _MODAL.search(text)
    if mm:
        out.append((mm.start(), _MODAL_KIND, mm, len(mm.group(0).rstrip())))
    out.sort(key=lambda c: (c[0], -c[3], c[1]))
    return out


def _clause(sentence: str, start: int, end: int) -> Optional[dict[str, Any]]:
    """Lower the clause ``sentence[start:end]``; offsets in the result index ``sentence``."""
    text = sentence[start:end]
    cands = _candidates(text)
    if not cands:
        return None
    _, kind, hit, _ = cands[0]
    sub_link = None
    canonical = None
    if kind == _COPULA_KIND:
        m = hit
        subj_raw = text[:m.start()]
        obj_raw = text[m.end():].strip()
        relation, predicate, obj_src = _DEFAULT_RELATION, m.group(0).strip().lower(), obj_raw
        for name, pat in _RELATIONS:
            rm = pat.search(text)
            if rm:
                relation = name
                if "rel" in pat.groupindex and rm.group("rel"):
                    # keep the relation phrase ("part of") as the predicate
                    predicate = rm.group("rel").lower()
                    obj_src = _OBJ_LEAD.sub("", text[rm.end():].strip())
                break
        obj = _OBJ_LEAD.sub("", obj_src).strip(_TRIM)
        quant = _quantification(subj_raw)
        # an empty-quantifier subject ("no provider …") is itself a negative claim,
        # as is an object-side negation ("… is not a …").
        negated = quant == "empty" or bool(_NEG.search(obj_raw[:24]))
    elif kind == _ORDER_KIND:
        m, relation, ordering_canonical, converse = hit
        subj_raw = text[:m.start()]
        obj = _OBJ_LEAD.sub("", text[m.end():].strip()).strip(_TRIM)
        predicate = m.group(0).strip().lower()
        quant = _quantification(subj_raw)
        negated = quant == "empty"
        canonical = (ordering_canonical, converse)
    else:  # modal: strip the auxiliary, keep the propositional content
        m = hit
        subj_raw = text[:m.start()]
        vm = _VERB.match(text, m.end())
        if not vm:
            return None
        predicate = vm.group(1).lower()
        rest_start = vm.end()
        rest_end = len(text)
        for name, pat in _SUBORDINATE:
            sm = pat.search(text, rest_start)
            if sm and sm.start() < rest_end:
                rest_end = sm.start()
                s0, s1 = _trim(sentence, start + sm.end(), end)
                sub_link = (name, s0, s1)
        obj = _OBJ_LEAD.sub("", text[rest_start:rest_end].strip()).strip(_TRIM)
        relation = _DEFAULT_RELATION
        quant = _quantification(subj_raw)
        negated = quant == "empty" or bool(m.group("neg"))
    subject = clean_entity(subj_raw)
    if not subject or not obj:
        return None
    s0, s1 = _trim(sentence, start, end)
    return {
        "fact": {
            "subject": subject,
            "predicate": predicate,
            "object": obj,
            "dimension": _BINDING[relation],
            "negated": negated,
            "quantification": quant,
        },
        "relation": relation,
        "span": (s0, s1),
        "canonical": canonical,
        "subordinate": sub_link,
    }


def _has_cue(text: str) -> bool:
    """Whether ``text`` fires any of this grammar's own cues (copula, ordering,
    modal or clausal complement). A genuine content clause has none."""
    return bool(_COMPLEMENT.search(text)) or bool(_candidates(text))


def _content_clause(text: str, subject_raw: Any, candidates: Optional[list] = None,
                     registry: Optional[dict] = None) -> Optional[dict[str, Any]]:
    """Lower a content clause: an infinitive/bare-verb clause with no subject of
    its own, given a subject supplied out of band (a norm's bearer, e.g. the
    versum context key ``context['subject']`` -- see ``plane.produce``).

    ``candidates`` and ``registry`` are both optional and both default to
    ``None``; every call site that omits them (every call before this round,
    and ``plane.produce``'s own legacy path when ``context`` carries no
    ``'frame'``/``'registry'`` key) behaves EXACTLY as before this round --
    see this docstring's own sections below for what each one changes when
    supplied.

    ``candidates`` -- the enclosing frame's list of prior-mentioned entities
    (``plane.produce``'s ``context['frame'][-1]['candidates']``) -- makes an
    own-PRONOUN subject ambiguous, rather than read verbatim, when it lists
    more than one distinct (case-insensitively) candidate: this function then
    returns ``{"abstain_reason": "AMBIGUOUS_PRONOUN", "span": (s0, s1)}``
    instead of a claim, rather than guess which candidate the pronoun refers
    to. ``None`` or a single-candidate list leaves pronoun handling unchanged.

    ``registry`` -- the document's defined-terms registry
    (``plane.produce``'s ``context['registry']``, built by
    ``registry.build_registry``) -- rescues what would otherwise be a
    determiner-led common-noun abstention: when the clause opens with a
    determiner/quantifier NP (``clean_entity``'s lead-in set) whose head,
    once the determiner is stripped, matches a registry term (case
    -insensitively, exactly at that position), the clause is read as
    carrying that term as its OWN subject -- not the context/inherited one
    -- with the registry's lower-cased canonical term as the subject value
    (so "The controller", "the controller" and "THE CONTROLLER" all resolve
    to the identical ``"controller"``). If that matched entry is
    SHADOWED (the document defines the same term twice with a different
    meaning; ``registry[term]["shadowed"]``), this function abstains instead
    with ``{"abstain_reason": "DEFINITION_SHADOWED", "span": (s0, s1)}``
    rather than pick one of the two meanings. When no registry term matches
    (or ``registry`` is ``None``), the determiner-led clause abstains exactly
    as before this round (plain ``None``).

    A clause that ends up needing the out-of-band ``subject_raw`` (no own
    pronoun/named/registry subject) and finds it empty/falsy returns
    ``{"abstain_reason": "NO_BEARER", "span": (s0, s1)}`` instead of the
    ordinary empty-subject ``None`` -- but only ever reachable when a caller
    passes a falsy ``subject_raw`` on purpose (``plane.produce``'s new frame
    -aware path passes ``""`` when the frame stack carries no bearer at all);
    the legacy call shape (``subject_raw`` always a truthy string) never
    exercises this path. ``NO_BEARER`` is decided only after a verb is
    confirmed AND the object is GENUINE (see the "genuine object" paragraph
    further down): with no subject of any kind on hand, that shape test is
    the only thing standing between a real bearer-less content clause and a
    non-clause fragment ("Hello world.", "12345."), so it gates this decision
    alone. ``AMBIGUOUS_PRONOUN`` (see below) is decided only after a verb is
    confirmed AND the object is non-empty -- the pronoun subject itself is
    already unambiguous in shape, so the fuller "genuine object" test is not
    applied there; only the legacy ``NO_BEARER`` path lacks any other way to
    tell a real clause from a fragment. A fragment that never reaches a verb
    returns the ordinary ``None`` from that earlier check instead -- neither
    typed abstention ever fires on something that is not an actual clause.
    The out-of-band ``subject_raw`` path (a caller-supplied, truthy bearer,
    the legacy ``context['subject']``/inherited-frame-bearer shape) is gated
    by neither: once a bearer is already on hand, any non-empty object is
    enough, exactly as before ``NO_BEARER``/``AMBIGUOUS_PRONOUN`` existed.

    Fires only when ``text`` carries none of this grammar's own cues
    (``_has_cue``): a genuine content clause has none, by construction, once
    its parent norm's modal auxiliary has already been stripped elsewhere.
    This keeps the three ``lower() -> None`` paths untouched, since each of
    those already has a cue that merely fails downstream.

    A leading "not"/"never" (``_LEADING_NEG``) is stripped before the verb is
    read off, and never itself mistaken for the clause's bare verb; it sets
    the output's polarity negative regardless of what the object-side scan
    finds. This is the content clause's *own* polarity, recorded on the
    action-type output for reference: the deontic norm's own ``negation``
    axis remains the ought-side authority on whether the norm itself is
    negated (see ``plane.produce``'s docstring).

    A clause that, once any leading negation is stripped, opens with a
    PRONOUN (``_OWN_PRONOUN``: "they", "it", "he", "she", "we") or an
    EXACTLY two-word Title-Case NAMED subject (``_OWN_NAMED``, e.g. "Member
    States") whose first word is not itself a determiner/quantifier carries
    an unambiguous subject of its own: that pronoun/NP, verbatim (through
    ``clean_entity``), becomes the claim's subject -- never the out-of-band
    ``subject_raw`` -- and the clause's leading bare verb *after* that
    subject is the predicate, so the predicate never begins with or contains
    the subject token.

    A leading Title-Case run is NOT read as a named subject, and instead
    falls through to the ordinary bare-verb / determiner-abstention handling
    below -- exactly as the same clause in all lower case would -- in two
    cases: (a) the run is THREE OR MORE words ("Notify Member States",
    "Inform Data Subjects"): a clause's first word is capitalised whenever
    the clause opens a sentence, whether that word is a proper noun or an
    ordinary imperative verb, so a three-plus-word run is read as that
    sentence-initial capitalised imperative VERB in front of a genuine
    two-word name, never as a three-word name of its own; and (b) the run's
    first word is itself a determiner/quantifier ("The Court orders
    otherwise"): capitalised only because it opens the sentence, not because
    it names anyone, so this is the same determiner-led common-noun subject
    as "the court orders otherwise" and must abstain the same way.
    Capitalisation therefore never flips a determiner-led abstention into a
    named-subject match: "The Court orders otherwise" and "the court orders
    otherwise" take the identical path through this function and return the
    identical result. This is the fix this docstring describes.

    A clause that, once any leading negation is stripped, still opens with a
    determiner/quantifier (``clean_entity``'s own lead-in set, e.g. "the",
    "a", "every") -- a common-noun subject such as "the reviewer" or "the
    court" -- is read as carrying its *own* subject NP too, but there is no
    cue-free way to tell where such a multi-word common-noun subject ends
    and its verb begins without guessing (unlike a closed pronoun or a
    Title-Case proper noun, both unambiguous). Such a clause is never forced
    through the bare-verb reading with the context subject substituted in
    either: this function abstains (``None``) for it, exactly as before.

    Absent both an own-pronoun and an own-named subject, and absent a
    determiner/quantifier lead-in, the clause is read as a genuine bare
    verb/infinitive with no subject of its own: the leading bare verb is the
    predicate; everything after it is the object, trimmed the same way as
    every other clause kind (``_OBJ_LEAD``, then ``_TRIM``). There is no
    subject text of the clause's own, so quantification and the object-side
    negation scan read the object text instead of a subject (contrast every
    other clause kind, which reads ``subj_raw``); the same object-side scan
    is used for the own-pronoun/own-named subject cases (there being no
    quantifier/negation cue on a pronoun or proper noun either).
    ``relation`` is always ``_DEFAULT_RELATION`` ("predication"): a content
    clause carries no is-a/part-of/has-part/ordering cue of its own, so its
    dimension always comes from the clause's own relation -- the plane's
    default relation binding (RELATIONAL; see ``binding.json``) -- never
    from whatever relation/dimension the parent norm happens to carry.

    A two-word own-NAMED candidate (``_OWN_NAMED``) is only accepted when a
    verb token actually follows it (``_VERB`` matches what comes after the
    two-word run): "Member States ensure compliance ..." has one ("ensure"),
    so "Member States" is read as the subject as before. "Notify
    Commission." does NOT -- nothing but a sentence terminator follows the
    two-word run "Notify Commission" -- so this is not a subject-plus
    -predicate clause after all: it is the same sentence-initial capitalised
    imperative shape as the three-plus-word case above (an imperative VERB,
    "Notify", in front of a single-word capitalised OBJECT, "Commission"),
    and falls through to the ordinary bare-verb reading the same way, keeping
    the out-of-band/context subject. A two-word run that both is not
    determiner-led AND is followed by a verb remains an unambiguous named
    subject exactly as before.

    Returns ``None`` -- never a guessed or defaulted subject -- when: ``text``
    carries a cue of its own; once any leading negation is stripped the
    clause opens with its own determiner-led common-noun subject NP that no
    registry term rescues; no verb token opens the remaining text; the
    resolved subject (the clause's own pronoun/named/registry subject, or
    else ``subject_raw`` cleaned via ``clean_entity``) is not a non-empty
    string, or the object is empty, once a verb is confirmed and no typed
    abstention applies; or, on the ``NO_BEARER`` path specifically (no own
    subject AND no out-of-band ``subject_raw``), the object is not GENUINE
    (see below) -- this last check gates ONLY the ``NO_BEARER`` decision, not
    the ordinary subject-resolved return just described, and not
    ``AMBIGUOUS_PRONOUN`` either (which requires only a confirmed verb and a
    non-empty object, its pronoun subject already being unambiguous in
    shape). A GENUINE object is a multi-word span, a capitalised
    (proper-noun-like) span (e.g. "Commission" in "Notify Commission."), or a
    determiner-/quantifier-led span (e.g. "every rejection") -- never a
    single, bare, lower-case common word (e.g. "world" in "Hello world.",
    which is not a content clause at all and returns plain ``None`` here,
    same as "12345.", which never matches a verb token in the first place).
    With no subject of any kind on hand on the ``NO_BEARER`` path, this is
    the only thing standing between a real bearer-less content clause and a
    non-clause fragment, so it is checked only there -- a fragment that never
    reaches a verb (e.g. "It." with more than one candidate antecedent --
    there is no verb after "It") abstains as plain ``None``, not
    ``AMBIGUOUS_PRONOUN``, for the separate reason given above. A clause with
    an already-confirmed bearer (its own pronoun/named/registry subject, or a
    truthy out-of-band ``subject_raw`` -- the legacy ``context['subject']``/
    inherited-frame-bearer shape) is never subject to the GENUINE-object
    test: any non-empty object is enough for that path, exactly as it was
    before ``NO_BEARER``/``AMBIGUOUS_PRONOUN`` existed. Returns one of the
    typed ``{"abstain_reason": ..., "span": ...}`` dicts above (never plain
    ``None``) for the three cases those sections describe (an ambiguous
    pronoun, a shadowed registry definition, or a wholly absent bearer),
    each only once the clause is already confirmed to have a verb (and,
    for ``NO_BEARER``, a genuine object).

    On success, the returned dict carries two additional keys beyond ``fact``
    /``relation``/``span``/``canonical``/``subordinate``: ``bearer_local``,
    the clause's own subject (pronoun, named, or registry-rescued) when it
    has one, else ``None``; and ``bearer_inherited``, ``subject_raw`` cleaned
    when the clause has no own subject of its own, else ``None`` -- exactly
    one of the two is ever non-``None``. See ``plane.produce``'s ``bearer``
    output key.
    """
    if _has_cue(text):
        return None
    body = text
    prefix_negated = False
    nm = _LEADING_NEG.match(body)
    if nm:
        prefix_negated = True
        body = body[nm.end():]

    own_subject_raw = None
    ambiguous_pronoun = False
    pm = _OWN_PRONOUN.match(body)
    if pm:
        own_subject_raw = pm.group(0)
        rest_body = body[pm.end():]
        if candidates is not None:
            distinct = {c.strip().lower() for c in candidates
                        if isinstance(c, str) and c.strip()}
            if len(distinct) > 1:
                ambiguous_pronoun = True
    else:
        nmm = _OWN_NAMED.match(body)
        if nmm and len(nmm.group(0).split()) == 2 and not _LEAD.match(body):
            # exactly two Title-Case words, the first not itself a
            # determiner/quantifier, AND a verb actually follows the run: an
            # unambiguous named subject. Without a following verb ("Notify
            # Commission.") this is not a subject-plus-predicate clause at
            # all -- see this function's docstring -- so it falls through to
            # the ordinary bare-verb reading below instead.
            candidate_rest = body[nmm.end():]
            if _VERB.match(candidate_rest):
                own_subject_raw = nmm.group(0)
                rest_body = candidate_rest
            else:
                rest_body = body
        else:
            # either no Title-Case run at all, or one this function does not
            # read as a named subject: three-plus words (a sentence-initial
            # capitalised imperative verb in front of a genuine two-word
            # name, e.g. "Notify Member States") or a determiner-led run
            # capitalised only by sentence position (e.g. "The Court") --
            # fall through unchanged, exactly as the all-lower-case clause
            # would (see this function's docstring).
            rest_body = body

    if own_subject_raw is None and _LEAD.match(body):
        # opens with its own determiner-led common-noun subject NP: not a
        # bare verb clause, and not one of the two unambiguous own-subject
        # shapes above either. A registry term matching the NP head (case
        # -insensitively, right after the determiner) rescues this instead
        # of an unconditional abstention -- see this function's docstring.
        # A SHADOWED match abstains immediately here (this is a determiner
        # -led NP whose head is already known to resolve, so it is already
        # known to be a genuine clause) -- unlike AMBIGUOUS_PRONOUN/NO_BEARER
        # below, which must wait until a verb and object are confirmed.
        rescue = _registry_rescue(body, registry)
        if rescue is None:
            return None
        if rescue.get("abstain_reason"):
            s0, s1 = _trim(text, 0, len(text))
            return {"abstain_reason": rescue["abstain_reason"], "span": (s0, s1)}
        own_subject_raw = rescue["term"]
        rest_body = rescue["rest"]

    vm = _VERB.match(rest_body)
    if not vm:
        return None
    predicate = vm.group(1).lower()
    rest = rest_body[vm.end():]
    if own_subject_raw is not None:
        subject = clean_entity(own_subject_raw)
    else:
        subject = clean_entity(subject_raw) if isinstance(subject_raw, str) else ""
    obj = _OBJ_LEAD.sub("", rest.strip()).strip(_TRIM)

    if ambiguous_pronoun:
        # An ambiguous own-pronoun subject already has an unambiguous SHAPE
        # (the closed pronoun set) and a confirmed verb (``vm`` above); the
        # only thing left to rule out is a lone pronoun with nothing after it
        # at all ("It." -- no object survives the verb match), which is not a
        # clause to be ambiguous about in the first place. The fancier
        # "genuine object" shape test just below (multi-word / capitalised /
        # determiner-led) is NOT applied here: it exists only to keep
        # NO_BEARER from firing on a non-clause fragment when there is no
        # subject at all to already confirm genuineness (see the NO_BEARER
        # branch below), not to second-guess an already-unambiguous pronoun
        # subject's object.
        if not obj:
            return None
        s0, s1 = _trim(text, 0, len(text))
        return {"abstain_reason": "AMBIGUOUS_PRONOUN", "span": (s0, s1)}

    if own_subject_raw is None and not subject_raw:
        # no own subject of any kind, and no out-of-band bearer either --
        # abstain with a typed reason rather than the ordinary empty-subject
        # ``None`` below (only ever reached when a caller passes a falsy
        # ``subject_raw`` on purpose; see this function's docstring). This is
        # the ONE decision the "genuine object" shape test gates: a genuine
        # content clause's object is either multi-word, a capitalised
        # (proper-noun-like) span ("Commission" in "Notify Commission."), or
        # itself determiner/quantifier-led ("every rejection") -- never a
        # single, bare, lower-case common word ("world" in "Hello world.").
        # With no subject of any kind to already confirm this is a genuine
        # clause, that shape test is what keeps NO_BEARER from firing on a
        # non-clause fragment such as "Hello world." or "12345.". It never
        # gates the legacy ``context['subject']`` path below (that path
        # already has a confirmed bearer, so any non-empty object is enough,
        # exactly as before this fix) nor the AMBIGUOUS_PRONOUN decision
        # above.
        genuine_object = bool(obj) and (
            len(obj.split()) > 1 or obj[0].isupper() or bool(_LEAD.match(rest.lstrip())))
        if not genuine_object:
            return None
        s0, s1 = _trim(text, 0, len(text))
        return {"abstain_reason": "NO_BEARER", "span": (s0, s1)}

    if not subject or not obj:
        return None
    quant = _quantification(rest)
    negated = prefix_negated or quant == "empty" or bool(_NEG.search(rest[:24]))
    s0, s1 = _trim(text, 0, len(text))
    return {
        "fact": {
            "subject": subject,
            "predicate": predicate,
            "object": obj,
            "dimension": _BINDING[_DEFAULT_RELATION],
            "negated": negated,
            "quantification": quant,
        },
        "relation": _DEFAULT_RELATION,
        "span": (s0, s1),
        "canonical": None,
        "subordinate": None,
        "bearer_local": subject if own_subject_raw is not None else None,
        "bearer_inherited": None if own_subject_raw is not None else subject,
    }


def _registry_rescue(body: str, registry: Optional[dict]) -> Optional[dict[str, Any]]:
    """A determiner-led common-noun NP at the start of ``body`` (already
    known to match ``_LEAD``), rescued against ``registry``: the longest
    registry term matching, case-insensitively and at a word boundary, right
    after the stripped determiner. Returns ``None`` when ``registry`` is
    falsy or no term matches (the caller abstains, unchanged from before this
    round); ``{"abstain_reason": "DEFINITION_SHADOWED"}`` when the matched
    term is shadowed; otherwise ``{"term": <registry key>, "rest": <text
    after the matched term>}``."""
    if not registry:
        return None
    lead_m = _LEAD.match(body)
    after_lead = body[lead_m.end():]
    best_term = None
    best_len = -1
    for term_lower, entry in registry.items():
        if not isinstance(term_lower, str) or not term_lower:
            continue
        tm = re.match(re.escape(term_lower) + r"\b", after_lead, re.I)
        if tm and len(term_lower) > best_len:
            best_term, best_len = term_lower, len(term_lower)
            best_entry = entry
    if best_term is None:
        return None
    if isinstance(best_entry, dict) and best_entry.get("shadowed"):
        return {"abstain_reason": "DEFINITION_SHADOWED"}
    return {"term": best_term, "rest": after_lead[best_len:]}


def _analyse(sentence: str) -> Optional[dict[str, Any]]:
    """The factual reading of ``sentence`` with its span, or ``None``.

    A clausal complement ("X knows that P") is not a fact about X: only P is
    lowered, over its own sub-span. Otherwise the whole sentence is the clause."""
    if not isinstance(sentence, str) or not sentence.strip():
        return None
    cm = _COMPLEMENT.search(sentence)
    if cm:
        return _clause(sentence, cm.end(), len(sentence))
    return _clause(sentence, 0, len(sentence))


def lower(sentence: str) -> Optional[dict[str, Any]]:
    """Lower an assertion into a 5D edge, or ``None`` on one of three paths.

    A copula, ordering or modal sentence lowers; a clausal complement lowers only
    its embedded clause. ``None`` is returned when: (1) no copula, ordering or
    modal cue fires at all (e.g. "Every controller keeps a record."); (2) a
    modal cue fires but no verb token follows it; or (3) the extracted subject
    or object is empty once trimmed (e.g. "The controller is.", "Must
    comply.")."""
    rec = _analyse(sentence)
    return dict(rec["fact"]) if rec else None
