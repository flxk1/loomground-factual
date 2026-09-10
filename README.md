<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 flxk1 -->
# loomground-factual

Assertoric language plane: lowers a copula-form assertion into a fixed 5D edge; the fact representation the modal planes evaluate against.

## Problem

Sentences enter the graph as text; nothing can reason over them. Lowers a sentence to subject, predicate, object with a dimension.

## Install

```
pip install "loomground-factual @ git+https://github.com/flxk1/loomground-factual@factual-v0.1.0"
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

A plain assertion as subject · predicate · object with a dimension (`structural` for is-a and part-of, `relational` for any other copula), polarity and quantification. Cue classes: structural predicate · copula (`is`, `are`, `shall be`, `means`, `includes`, `consists of`, `refers to`) · negation · quantifier (universal, existential, empty) · entity trimming.

```
The operator is a controller.            operator · is · controller · structural · existential
A processor is not a controller.         processor · is · controller · structural · negated · existential
Every controller is a natural person.    controller · is · natural person · structural · universal
The register consists of entries.        register · consists of · entries · relational · existential
```

Full card: `docs/language-card.md`.

## Interface

| Item | Definition |
|---|---|
| Input | one sentence (`str`) |
| `lower(sentence)` | `None` for a sentence without a copula; else a dict: `subject`, `predicate`, `object`, `dimension`, `negated`, `quantification` |
| `dimension` | `structural` for is-a / part-of predicates, else `relational` |
| `quantification` | `universal`, `existential`, `empty` |
| `clean_entity(span)` | reduces a span to its NP head; shared with the deontic bearer and the epistemic holder |
| `load_json(name)` | packaged artifact loader |
| `artifacts/extraction.json` | every cue as data: copula, structural, negation, quantifier, entity markers |

## Family

Assertoric base language; the fact representation consumed by modal planes. A fact is a relation between entities, so it lowers onto the 5D floor without an nD facet. The plane lowers only; composition and reasoning live on `loomground-solver`.

- Consumes: nothing at runtime.
- Consumed by: `loomground-epistemic` (`loomground-factual>=0.1,<0.2`, for `clean_entity`).
- Modal planes over this base: `loomground-deontic` (ought), `loomground-epistemic` (know/believe).
- Pipeline: `source → loomground-ingest → loomground-versum → loomground-solver → applied or diagnostic planes`; the base representation assertions lower into.

Positioning and prior art: `docs/positioning.md`.

## Status

0.1.0 · 1 test · Python ≥ 3.10 (CI 3.12) · standard library only.

## License

Apache-2.0 — `LICENSES/Apache-2.0.txt`, `NOTICE`; `REUSE.toml`.
