---
name: factual
description: 'Lower one plain assertion into a factual triple: subject, predicate, object, with dimension (structural for is-a, part-of and has-part; temporal for an ordering such as "follows" or "comes before"; relational for any other predicate, including the propositional content of a modal sentence), negation and quantification. Use when the user wants a sentence read as a fact, asks what loomground-factual recognises (copulas, orderings, modal auxiliaries it strips, "knows that" complements, negation, quantifiers, entity trimming), or needs to know whether a sentence lowers at all; triggers on "lower this sentence", "is this a fact", "subject predicate object", "factual triple". Ought as a force, knowledge as an attitude, and authority belong to the other planes.'
allowed-tools: factual_lower
metadata:
  version: "1.1"
governance:
  grade: L1
  actions:
    - { kind: lower, risk: low }
  reserved: []
  prohibited:
    - guess_triple
  budget: { usd: 1, iters: 10 }
---

# loomground-factual — language card

Primary path: call `factual_lower` with `{"sentence": "The operator is a controller."}`; the `result` is `{subject, predicate, object, dimension, negated, quantification}`, and a sentence that lowers to `None` (no cue at all, a modal cue with no following verb token, or an empty subject/object) comes back `unavailable`, never as a guessed triple.

Shell fallback: `python3 -c 'from loomground_factual import lower; print(lower("The operator is a controller."))'` (package `loomground-factual`; `None` on one of three paths — see "Output" below).

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

The plane descriptor (`loomground_factual.plane:plane`, entry-point group `loomground.planes`, id `factual`) publishes an nD system `loomground-factual` with five axes (`subject`, `predicate`, `object` open; `polarity`, `quantification` closed), the binding above, a pure producer `produce(sentence) → [claim]` (at most one claim; `[]` when no fact), and conformance examples. This `nd_system` is what gets **registered as an nD system on the versum index**: a versum host discovers the plane via the `loomground.planes` entry-point and registers the descriptor's `nd_system` under id `factual`; this package never registers itself, it only publishes the descriptor.

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

## Outside the language

Ought as a force (`loomground-deontic`; this plane keeps only the propositional content of a modal sentence), knowledge and belief as attitudes (`loomground-epistemic`; this plane lowers only the embedded clause), authority (`loomground-topos`). Time is carried only as an ordering between two events (`temporal`); dates and durations are out of scope. `lower` returns `None` on three paths: a sentence with no copula, ordering or modal cue at all (a plain verb such as `keeps`); a modal cue with no verb token following it; or an empty subject or object once trimmed.

Same card, README-linked copy: `../../docs/language-card.md`.
