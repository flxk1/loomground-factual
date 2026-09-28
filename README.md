<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 flxk1 -->
# loomground-factual

Assertoric language plane: lowers a copula, ordering or modal assertion into a fixed 5D edge and publishes the factual nD system; the fact representation the modal planes evaluate against.

## Problem

Sentences enter the graph as text; nothing can reason over them. Lowers a sentence to subject, predicate, object with a dimension.

## Install

```
pip install "loomground-factual @ git+https://github.com/flxk1/loomground-factual@factual-v0.2.0"
```

Dependents pin `loomground-factual>=0.1,<0.2`.

## Usage

```python
from loomground_factual import lower, clean_entity

lower("The register consists of entries.")
# {'subject': 'register', 'predicate': 'consists of', 'object': 'entries',
#  'dimension': 'relational', 'negated': False, 'quantification': 'existential'}

clean_entity("Where applicable, the processor")   # 'processor'
```

## Example

```
in : lower("The operator is a controller.")
out: {'subject': 'operator', 'predicate': 'is', 'object': 'controller', 'dimension': 'structural', 'negated': False, 'quantification': 'existential'}
```

## Language

A plain assertion as subject · predicate · object with a dimension, polarity and quantification. Three sentence shapes lower: a copula (`predicate_cues.copula`: `is`, `are`, `shall be`, `means`, `includes`, `consists of`, `refers to`), refined by `predicate_cues.relations` into is-a, part-of or has-part (`structural`); an ordering (`ordering_cues`: `precedes`, `comes before`, `is followed by`, `follows`, `comes after`, `succeeds` …; `temporal`, published canonically as `precedes`); and a modal sentence (`modal_cues`: `must`, `shall`, `may`, `can` / `cannot`, `is required to`, `has to`, `ought to` …, each optionally followed directly by `not`, e.g. `must not`, `cannot`), whose auxiliary is stripped so the next verb becomes the predicate (`relational`). `complement_cues` (`knows that`, `believes that`, `is aware that` …) lower only the embedded clause, over its own sub-span. When two cues start at the same offset the longest wins (`is required to` over `is`). Further cue classes: negation · quantifier (universal, existential, empty) · entity trimming.

`is/are required to` fires the modal cue only when contiguous. Putting `not` on either side of `required` — "is not required to", "is required not to" — breaks that contiguity, so those two phrasings fall through to the plain copula cue (`is`/`are`) instead: the copula stays in the predicate and `required (not) to …` stays in the object. `negated` still comes out `true` for both, because the copula path's own object-side negation scan still finds `not`. This is the code's actual behaviour, not the intended target; a fix belongs in `artifacts/extraction.json`'s `modal_cues.modal` pattern.

```
The operator is a controller.            operator · is · controller · structural · existential
A processor is not a controller.         processor · is · controller · structural · negated · existential
The scoring model is part of the credit system.
                                         scoring model · part of · credit system · structural · existential
The register consists of entries.        register · consists of · entries · relational · existential
The review follows the automated scoring.
                                         review · follows · automated scoring · temporal · existential
A controller is required to notify the authority.
                                         controller · notify · authority · relational · existential
The provider cannot refuse access.       provider · refuse · access · relational · negated · existential
Every controller keeps a record.         None  (no copula, ordering or modal cue)
```

Full card: `docs/language-card.md`.

## Interface

| Item | Definition |
|---|---|
| Input | one sentence (`str`) |
| `lower(sentence)` | a dict (`subject`, `predicate`, `object`, `dimension`, `negated`, `quantification`), or `None` on one of three paths: no copula, ordering or modal cue fires at all; a modal cue fires but no verb token follows it; or the extracted subject or object is empty once trimmed. A modal auxiliary (`must`, `shall`, `may`, `cannot`, `is required to` …) is stripped to the propositional content; a clausal complement (`knows that …`) lowers only its embedded clause |
| `dimension` | `structural` for is-a / part-of / has-part, `temporal` for an ordering (precedes / follows), `relational` for any other predicate (`predication`) |
| `quantification` | `universal`, `existential`, `empty` |
| `clean_entity(span)` | reduces a span to its NP head; shared with the deontic bearer and the epistemic holder |
| `load_json(name)` | packaged artifact loader |
| `plane()` | the plane descriptor (entry-point group `loomground.planes`, id `factual`): nD system `loomground-factual` (axes `subject`, `predicate`, `object`, `polarity`, `quantification`), the 5D binding, the pure producer `produce(sentence, context=None) → [claim]` and conformance examples. This `nd_system` is what gets **registered as an nD system on the versum index**: a versum host discovers the plane via the `loomground.planes` entry-point and registers the descriptor's `nd_system` under id `factual`; this package never registers itself, it only publishes the descriptor |
| `produce(sentence, context)` | `context` is ignored for every sentence the plane already lowers on its own (its output, including every published example, is unaffected by whatever `context` carries). Set `context['subject']` (a non-empty string — a norm's bearer; versum sets it from the parent norm's bearer) to lower a **content clause**: an infinitive/bare-verb clause with no subject of its own (e.g. `"make a solely automated decision on a credit application"`). The clause's leading bare verb becomes the predicate, the rest (leading-determiner stripped) the object, the relation always comes from the clause's own relations only — `predication` (dimension `relational`). This claim is an **action type, not an asserted fact**: it carries `asserted: False`, `entry_kind: "action_type"` and its own method label `"loomground-factual/content_clause"` (never the plain `"loomground-factual/lower"` label an asserted fact gets); a leading "not"/"never" keeps negative polarity on it. Fires only on a clause with none of the grammar's own cues. A clause that carries its own subject — a closed pronoun (`they`, `it`, `he`, `she`, `we`) or an exactly-two-word Title-Case named subject whose first word is not itself a determiner (e.g. `"Member States"`) — keeps that subject, never the context one, with the predicate starting strictly after it. Sentence-initial capitalisation alone is never enough to read a named subject: a THREE-OR-MORE-word leading Title-Case run (e.g. `"Notify Member States without delay"`) is a sentence-initial capitalised imperative verb in front of a genuine two-word name — the context subject is kept, the verb becomes the predicate, exactly as if the clause opened in lower case — and a leading Title-Case run whose first word is itself a determiner (e.g. `"The Court orders otherwise"`) abstains exactly as its lower-case form does (`"the court orders otherwise"` and `"The Court orders otherwise"` are identical). A clause with a determiner-led common-noun subject of its own (e.g. `"the reviewer"`, `"the court"`) still abstains, since there is no cue-free way to split such a subject from its verb without guessing. A missing `context`, a missing/falsy/non-string `subject`, or a clause with its own cue, all leave the output exactly as before. See `docs/language-card.md` |
| `artifacts/extraction.json` | every cue as data: `predicate_cues.copula`, `predicate_cues.relations` (is-a, part-of, has-part), `ordering_cues`, `modal_cues` (auxiliaries, temporal subordinates), `complement_cues`, negation, quantifiers, entity trimming |
| `artifacts/binding.json` | the relation → 5D binding, its one home |

## Family

Assertoric base language; the fact representation consumed by modal planes. A fact is a relation between entities, so it lowers onto the 5D floor; its coordinates (subject, predicate, object, polarity, quantification) are published as the nD system `loomground-factual`. The plane lowers only; composition and reasoning live on `loomground-solver`.

- Consumes: nothing at runtime.
- Consumed by: `loomground-epistemic` (`loomground-factual>=0.1,<0.2`, for `clean_entity`).
- Modal planes over this base: `loomground-deontic` (ought), `loomground-epistemic` (know/believe).
- Pipeline: `source → loomground-ingest → loomground-versum → loomground-solver → applied or diagnostic planes`; the base representation assertions lower into.

Positioning and prior art: `docs/positioning.md`.

## Status

0.2.0 · 136 tests · Python ≥ 3.10 (CI 3.12) · standard library only.

## How this is made

The code and documentation are written with Loomground agents. The maintainer reads and corrects all of it.

## License

Apache-2.0 — `LICENSES/Apache-2.0.txt`, `NOTICE`; `REUSE.toml`.
