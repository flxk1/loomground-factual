<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 flxk1 -->
# loomground-factual — language card

Cues from `src/loomground_factual/artifacts/extraction.json` (0.1.0); the relation → 5D binding from `src/loomground_factual/artifacts/binding.json`; the plane has no keywords. Every sentence below was run through `lower` before this card was written; the outputs are pasted from that run.

## What it recognises in one sentence

Three sentence shapes lower: a **copula** sentence, an **ordering** sentence and a **modal** sentence. A **clausal complement** lowers only its embedded clause. When two cues start at the same offset, the longest cue wins (`is required to` and `is followed by` over `is`; `shall be` over `shall`); otherwise the earliest cue in the sentence wins.

| cue class (`extraction.json` key) | cue words | effect |
|---|---|---|
| copula (`predicate_cues.copula`) | `is` · `are` · `shall be` · `means` · `include` / `includes` / `included` · `consists of` / `consist of` · `refers to` / `refer to` | subject before the cue, object after it; the cue is the predicate; relation `predication` → dimension `relational` unless a `predicate_cues.relations` cue also matches |
| is-a (`predicate_cues.relations.is-a`) | `is a` · `is an` · `is one of` · `is a type of` · `is a kind of` · `is a category of` (also with `are`, `shall be`, and an intervening `not`) | relation `is-a` → dimension `structural`; predicate stays the copula (`is`, `are`, `shall be`) |
| part-of (`predicate_cues.relations.part-of`) | `is part of` (also `are`, `shall be`, `not`) | relation `part-of` → `structural`; predicate `part of` |
| has-part (`predicate_cues.relations.has-part`) | `is comprised of` · `is composed of` (also `are`, `shall be`, `not`) | relation `has-part` → `structural`; predicate `comprised of` / `composed of` |
| ordering (`ordering_cues`) | precedes: `precede(s)` · `come(s) before` · `take(s) place before` · `is / are followed by`; follows: `follow(s)` · `come(s) after` · `take(s) place after` · `succeed(s)` | relation `precedes` / `follows` → dimension `temporal`; `lower` keeps the surface predicate; `produce` publishes the canonical `precedes` claim (`X follows Y` → `Y precedes X`) |
| modal (`modal_cues.modal`) | `must` · `shall` · `should` · `may` · `can` · `cannot` · `could` · `might` · `will` · `would` · `is / are required to` · `has / have to` · `ought to`, each optionally followed *directly* by `not` (e.g. `must not`, `cannot`) | the auxiliary is stripped: the next verb is the predicate, the rest the object; relation `predication` → `relational`; `not` (or `cannot`) → `negated: true`. The deontic force itself belongs to `loomground-deontic`. `is / are required to` is this cue only when contiguous: `is not required to` and `is required not to` break the contiguity and do not fire this cue at all (see below) |
| temporal subordinate (`modal_cues.temporal_subordinate`) | precedes: `before` · `prior to` · `until`; follows: `after` · `once` · `following` | inside a modal sentence, cuts the object at the subordinate clause; `produce` adds a `temporal` link to the clause's span |
| clausal complement (`complement_cues.clausal_complement`) | `know(s)` · `believe(s)` · `is / are aware` · `become(s) aware` · `consider(s)` · `find(s)` · `state(s)` · `establishes / established` · `hold(s)` · `is / are satisfied`, each followed by `that` | only the clause after `that` is lowered, over its own sub-span; the attitude itself belongs to `loomground-epistemic` |
| negation (`polarity_cues.negation`) | `not` · `no` · `never` · `neither` · `without` (in the first words of a copula object) | `negated: true` |
| universal quantifier | `all` · `any` · `every` · `each` (in the subject) | `quantification: universal` |
| existential quantifier | `some` · `a` · `an`, and the default | `quantification: existential` |
| empty quantifier | `no` · `none of` · `neither` (in the subject) | `quantification: empty`, and `negated: true` |
| entity trimming (`entity_cues`) | leading list markers and numbering; leading `a / an / the / its / their / any / this / each / every / all / both / such / no` (also `der / die / das / ein / eine / jede`); trailing `which / who / whose / to which / as referred to / referred to in / pursuant to / adopted by / involved in …` | clean subject and object |

Dimension binding (`binding.json`, the one home): `is-a`, `part-of`, `has-part` → `structural`; `precedes`, `follows` → `temporal`; `predication` → `relational`.

**"is not required to" / "is required not to".** The modal cue's `is / are required to` alternative only fires when the three words are contiguous. Putting `not` on either side of `required` breaks that contiguity, so `is not required to …` and `is required not to …` fall through to the plain copula cue (`is` / `are`) instead: the copula stays as the predicate and `required (not) to …` stays inside the object (the auxiliary is *not* stripped, unlike the plain `is required to`). `negated` still comes out `true` for both, because the copula path's own object-side negation scan still finds `not`. This is the code's documented behaviour, not the target behaviour; a proper fix belongs in `artifacts/extraction.json`'s `modal_cues.modal` pattern.

```
The provider is required to comply with the code.
                                         provider · comply · with the code · relational · existential
The provider is not required to comply with the code.
                                         provider · is · not required to comply with the code · relational · negated · existential
The provider is required not to comply with the code.
                                         provider · is · required not to comply with the code · relational · negated · existential
```

## Output

`lower(sentence) → {subject, predicate, object, dimension, negated, quantification}`, or `None` on one of three paths: (1) no copula, ordering or modal cue fires anywhere in the (sub-)clause; (2) a modal cue fires but no verb token follows it; (3) the extracted subject or object is empty once trimmed. `clean_entity(span)` reduces a span to its NP head with the entity cues; `load_json(name)` loads a packaged artifact.

The plane descriptor (`loomground_factual.plane:plane`, entry-point group `loomground.planes`, id `factual`) publishes an nD system `loomground-factual` with five axes (`subject`, `predicate`, `object` open; `polarity`, `quantification` closed), the binding above, a pure producer `produce(sentence) → [claim]` (at most one claim; `[]` when no fact), and conformance examples. This `nd_system` document is what gets **registered as an nD system on the versum index**: a versum host discovers the plane via the `loomground.planes` entry-point (id `factual`) and registers the descriptor's `nd_system` under that id on its own nD-system index; this package never registers itself, it only publishes the descriptor.

## Readings

```
The operator is a controller.            operator · is · controller · structural · existential
A processor is not a controller.         processor · is · controller · structural · negated · existential
Every controller is a natural person.    controller · is · natural person · structural · universal
No processor is a controller.            processor · is · controller · structural · negated · empty
The scoring model is part of the credit system.
                                         scoring model · part of · credit system · structural · existential
The register consists of entries.        register · consists of · entries · relational · existential
The review follows the automated scoring.
                                         review · follows · automated scoring · temporal · existential
A controller is required to notify the authority.
                                         controller · notify · authority · relational · existential
The provider cannot refuse access.       provider · refuse · access · relational · negated · existential
The controller knows that the training data is inaccurate.
                                         training data · is · inaccurate · relational · existential
Every controller keeps a record.         None  (no copula, ordering or modal cue)
```

Outputs as returned:

```
{'subject': 'operator', 'predicate': 'is', 'object': 'controller', 'dimension': 'structural', 'negated': False, 'quantification': 'existential'}
{'subject': 'processor', 'predicate': 'is', 'object': 'controller', 'dimension': 'structural', 'negated': True, 'quantification': 'existential'}
{'subject': 'controller', 'predicate': 'is', 'object': 'natural person', 'dimension': 'structural', 'negated': False, 'quantification': 'universal'}
{'subject': 'processor', 'predicate': 'is', 'object': 'controller', 'dimension': 'structural', 'negated': True, 'quantification': 'empty'}
{'subject': 'scoring model', 'predicate': 'part of', 'object': 'credit system', 'dimension': 'structural', 'negated': False, 'quantification': 'existential'}
{'subject': 'register', 'predicate': 'consists of', 'object': 'entries', 'dimension': 'relational', 'negated': False, 'quantification': 'existential'}
{'subject': 'review', 'predicate': 'follows', 'object': 'automated scoring', 'dimension': 'temporal', 'negated': False, 'quantification': 'existential'}
{'subject': 'controller', 'predicate': 'notify', 'object': 'authority', 'dimension': 'relational', 'negated': False, 'quantification': 'existential'}
{'subject': 'provider', 'predicate': 'refuse', 'object': 'access', 'dimension': 'relational', 'negated': True, 'quantification': 'existential'}
{'subject': 'training data', 'predicate': 'is', 'object': 'inaccurate', 'dimension': 'relational', 'negated': False, 'quantification': 'existential'}
None
```

## Content clauses: an action type, lowered with a subject from context

`lower()` never takes a subject from outside the sentence. `plane.produce(sentence, context)` does, for exactly one case: a **content clause** — an infinitive/bare-verb clause with no subject of its own (e.g. "make a solely automated decision on a credit application", the propositional content of a norm once its modal auxiliary and bearer have already been peeled off elsewhere). Set `context['subject']` to a non-empty string (the norm's bearer; versum sets it from the parent norm's bearer) and a clause with none of this grammar's own cues lowers: the clause's leading bare verb is the predicate, the rest of the clause (leading-determiner stripped, same as every other clause kind) is the object, and the given subject is used verbatim — *unless* the clause carries an own subject of its own (see below), in which case that subject is used instead.

**A clause may carry its own subject instead of the context one.** A closed pronoun ("they", "it", "he", "she", "we") or an exactly-two-word Title-Case named subject whose first word is not itself a determiner (e.g. "Member States") at the start of the clause (once any leading "not"/"never" is stripped) is read off, verbatim, as that claim's subject — never the context subject — with the predicate starting strictly after it, so the predicate never begins with or contains the subject token.

Sentence-initial capitalisation alone is never enough to read a named subject: a clause's first word is capitalised whenever it opens a sentence, whether that word is a proper noun or an ordinary imperative verb. So a THREE-OR-MORE-word leading Title-Case run ("Notify Member States without delay", "Inform Data Subjects of the breach") is read as a sentence-initial capitalised imperative verb in front of a genuine two-word name, not a three-word name of its own — the context subject is kept and the verb becomes the predicate, exactly as if the clause had opened in lower case. A leading Title-Case run whose first word is itself a determiner ("The Court orders otherwise") is read as the same determiner-led common-noun subject as its lower-case form and abstains the same way: "the court orders otherwise" and "The Court orders otherwise" produce the identical result. A determiner-led common-noun subject ("the reviewer", "the court") is also read as carrying its own subject, but there is no cue-free way to split such a multi-word common-noun span from its verb without guessing, so that shape still abstains (`[]`) rather than guess or borrow the context subject.

**This is an action type, not an asserted fact.** The sentence never asserted it — there is nothing in the content clause itself to have observed a fact from; the subject was supplied out of band (or read off the clause's own pronoun/named subject). The claim carries `asserted: False`, `entry_kind: "action_type"`, and its own method label `"loomground-factual/content_clause"` (`plane.METHOD_ACTION_TYPE`) — never the plain `"loomground-factual/lower"` label an asserted fact gets. Its `coordinates["polarity"]` still records the clause's own polarity (negative when the clause opens with "not"/"never", or its object carries the plane's own negation/empty-quantifier cues), kept for reference on the action type; it is not the ought-side authority on whether the parent norm itself is negated — that authority is the deontic norm's own `negation` axis (`loomground-deontic`). A consumer reads the norm's `negation` for the norm's polarity and this claim's `polarity` only for the action type's own.

This path activates when EITHER `context['subject']` is a non-empty string OR `context['frame'][-1]['bearer']` is a non-empty string (a frame bearer alone, with no `'subject'` key in `context` at all, is enough — see "Subject resolution: the defined-terms registry and the frame stack" below; when both are given, the frame bearer supersedes the legacy `context['subject']` shorthand). A missing `context`, an empty dict, or a `context` whose `'subject'` key and `'frame'` bearer are both missing/falsy/non-string all leave the clause exactly as before (`[]`, since a bare content clause has no cue of its own to fire `lower()`'s ordinary three paths). A sentence that already lowers on its own (a copula, ordering or modal sentence, or a clausal complement) ignores `context` entirely: its output, including every published example, is unaffected by whatever `context` carries, and never picks up the action-type flags. The producer never fabricates a subject from the clause itself when it has none of its own (there is none) or from a default bearer; a wrong or missing bearer never silently substitutes one.

```
make a solely automated decision on a credit application   + subject "controller"
                                         controller · make · solely automated decision on a credit application · relational · asserted: False, entry_kind: action_type
use the score to prepare a decision     + subject "controller"
                                         controller · use · score to prepare a decision · relational · asserted: False, entry_kind: action_type
examine every rejection                 + subject "reviewer"
                                         reviewer · examine · every rejection · relational · asserted: False, entry_kind: action_type
not disclose the source of the score    + subject "controller"
                                         controller · disclose · source of the score · relational · negated · asserted: False, entry_kind: action_type
they notify the data subject without delay   + subject "controller"
                                         they · notify · data subject without delay · relational · asserted: False, entry_kind: action_type  (own subject "they", not "controller")
Member States lay down the rules on penalties applicable to infringements   + subject "controller"
                                         Member States · lay · down the rules on penalties applicable to infringements · relational · asserted: False, entry_kind: action_type  (own subject "Member States", not "controller")
the court orders otherwise              + subject "controller"
                                         None  (a determiner-led common-noun subject of its own; abstains rather than guess where it ends and its verb begins, or borrow "controller")
Notify Member States without delay      + subject "controller"
                                         controller · notify · Member States without delay · relational · asserted: False, entry_kind: action_type  (sentence-initial capitalised imperative verb, NOT a named subject; "controller" is kept)
Inform Data Subjects of the breach      + subject "controller"
                                         controller · inform · Data Subjects of the breach · relational · asserted: False, entry_kind: action_type  (same: "Inform" is the verb, not part of a three-word name)
The Court orders otherwise              + subject "controller"
                                         None  (identical to "the court orders otherwise": capitalisation never flips the determiner-led abstention)
```

## Subject resolution: the defined-terms registry and the frame stack

Two more optional, additive `context` keys carry a document's own subject-resolution data into `plane.produce()` -- both leave the pre-existing behaviour (this card's other sections) exactly unchanged when omitted, and neither changes `produce`'s signature or any pre-existing output key.

**`context['registry']`** -- the document's defined-terms registry, built once per document by `build_registry(document_text)` (`loomground_factual.build_registry`, also `registry.build_registry`). Three sentence shapes populate it, each tried once per sentence, in this order:

| pattern | example | term key |
|---|---|---|
| quoted, colon/dash-led | `"Controller": the natural or legal person which determines the purposes of processing.` | `controller` |
| `hereinafter (referred to as) "X"` | `The natural or legal person who determines the purposes of processing (hereinafter referred to as the "Controller").` | `controller` |
| plain `X means ...` | `Controller means the natural or legal person who determines the purposes of processing.` | `controller` |

A term key is case- and leading-article-insensitive (`"The Controller"`, `"controller"`, `"CONTROLLER"` all key the same entry). A term defined twice in the same document with a DIFFERENT meaning (compared after whitespace normalisation) is marked `shadowed: True` on that entry; defined twice with the identical meaning, it is not.

**`context['frame']`** -- a FRAME STACK: a list of frame dicts, outermost first, `context['frame'][-1]` enclosing the current sentence. A frame dict is `{"bearer": <str or None>, "candidates": <list[str] or None>}`. `frame[-1]['bearer']` is this sentence's inherited bearer -- it SUPERSEDES the older single-frame `context['subject']` shorthand when both are given (`{"subject": "old", "frame": [{"bearer": "new", ...}]}` inherits `"new"`, not `"old"`), and `context['subject']` alone still works exactly as before when no `'frame'` key is given; `frame[-1]['candidates']` is the frame's list of prior-mentioned entities, consulted only to judge whether a pronoun subject is ambiguous.

Supplying either key switches `produce` into frame-aware mode for one more case: a bare content clause with no bearer available at all (no own subject, no registry rescue, and an empty/falsy inherited bearer) abstains with the typed reason `NO_BEARER` instead of the plain `[]` the legacy shape (no `context`, or `context` with at most `'subject'`) still returns.

**Every produced claim carries a `bearer` key**, `{"local": ..., "inherited": ...}`, exactly one of the two ever non-`None`:

| subject shape | example | `bearer` |
|---|---|---|
| an asserted claim (this plane's own copula/ordering/modal/clausal-complement reading) | `"The bank is a controller."` | `{"local": "bank", "inherited": None}` |
| an imperative with no subject of its own | `"Notify Commission."`, `"Inform Data Subjects of the breach."` | `{"local": None, "inherited": <frame bearer>}` |
| a pronoun or a registry-rescued term | `"they notify the data subject"`, `"the controller notifies the authority"` (registry defines `controller`) | `{"local": "they"}` / `{"local": "controller"}`, `"inherited": None` |

A determiner-led common-noun subject ("the reviewer", "the controller") still abstains, unchanged, UNLESS its head matches a registry term, in which case it resolves to that term case-insensitively -- `"The controller"`, `"the controller"` and `"THE CONTROLLER"` all resolve to the identical `bearer["local"] == "controller"`.

**Abstention with a typed reason.** Three situations abstain rather than guess, each reported as a ONE-ELEMENT list -- `[{"abstained": True, "reason": <code>, "span": [s0, s1]}]` -- never a claim dict (no `coordinates`/`relation`/`method`):

| reason code | trigger |
|---|---|
| `AMBIGUOUS_PRONOUN` | a pronoun subject, with more than one distinct candidate antecedent in `context['frame'][-1]['candidates']` |
| `DEFINITION_SHADOWED` | a determiner-led subject resolves to a registry term whose entry is `shadowed: True` |
| `NO_BEARER` | frame-aware mode (`context['frame']` or `context['registry']` supplied), a bare content clause, and no bearer of any kind available |

`NO_BEARER` only ever fires on an actual clause with no bearer of any kind: a confirmed bare verb followed by a GENUINE object (a multi-word span, a capitalised/proper-noun-like span such as `"Commission"`, or a determiner-/quantifier-led span such as `"every rejection"` -- never a single bare lower-case common word). With no subject at all on hand, this GENUINE-object shape test is the only way to tell a real bearer-less content clause from a non-clause fragment, so it gates the `NO_BEARER` decision alone -- `"Hello world."` and `"12345."` (frame bearer `None`) both return `[]`. `AMBIGUOUS_PRONOUN` fires on a confirmed bare verb with a non-empty object: the pronoun subject is already unambiguous in shape, so the fuller GENUINE-object test is not applied there -- `"It notifies authorities."` (candidates `["controller", "processor"]`) still abstains `AMBIGUOUS_PRONOUN` even though `"authorities"` is a single bare lower-case word. Neither typed reason ever fires on a fragment with no verb at all -- `"It."` (a pronoun with more than one candidate antecedent but nothing following it) returns `[]`, not `AMBIGUOUS_PRONOUN`. Neither typed reason applies to a clause that already has a bearer of its own (an own subject, or a truthy out-of-band/legacy `context['subject']`): that path lowers with any non-empty object, exactly as it always did -- `"Notify authorities."` with `context={"subject": "controller"}` still produces a claim, not `[]` or a typed abstention.

```
Notify Commission.                       + frame bearer "controller"
                                         controller · notify · Commission · relational · asserted: False, entry_kind: action_type
                                         bearer: {"local": None, "inherited": "controller"}
they notify the data subject             + frame bearer "controller", candidates ["controller"]
                                         they · notify · data subject · relational · asserted: False, entry_kind: action_type
                                         bearer: {"local": "they", "inherited": None}
they notify the data subject             + frame bearer "controller", candidates ["controller", "processor"]
                                         [{"abstained": True, "reason": "AMBIGUOUS_PRONOUN", "span": [...]}]
the controller notifies the authority    + registry {"controller": {"meaning": ..., "shadowed": False}}
                                         controller · notifies · authority · relational · asserted: False, entry_kind: action_type
                                         bearer: {"local": "controller", "inherited": None}
THE CONTROLLER notifies the authority    + same registry
                                         (identical result to the line above: case-insensitive)
the controller notifies the authority    + registry {"controller": {"meaning": ..., "shadowed": True}}
                                         [{"abstained": True, "reason": "DEFINITION_SHADOWED", "span": [...]}]
```

## Outside the language

Ought as a force (`loomground-deontic`; this plane keeps only the propositional content of a modal sentence), knowledge and belief as attitudes (`loomground-epistemic`; this plane lowers only the embedded clause), authority (`loomground-topos`). Time is carried only as an ordering between two events (`temporal`); dates and durations are out of scope. `lower` returns `None` on three paths: a sentence with no copula, ordering or modal cue at all (a plain verb such as `keeps`); a modal cue with no verb token following it; or an empty subject or object once trimmed.
