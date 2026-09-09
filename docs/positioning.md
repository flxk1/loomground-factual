<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 flxk1 -->
# Positioning & prior art

Moved verbatim from the README (introduction and "Positioning & prior art").

The **factual / assertoric** language plane of the Loomground family. It lowers
copula-form assertions into the family's fixed five-dimensional (5D) edge
representation — relational and structural edges — that the modal languages
evaluate against. It plays the *alethic* role in that family: the base plane that
says *what is the case*, over which the deontic (ought), epistemic (know/believe),
and legal planes reason. The mechanism itself is deliberately small — a narrow,
tailored regex copula/SPO extractor, not a general semantic parser; see below for
how it is scoped and what it is not.

Standard-library only. It is a leaf: it depends on no other Loomground plane at
runtime, and grows no reasoning of its own — composition and grounded reasoning
live on `loomground-solver`, the modal vocabularies on their own planes.

## Positioning & prior art

This plane is a deliberately narrow, standard-library-only extractor, chosen for a
local-first, zero-dependency, fully-auditable runtime rather than for breadth or
recall. Its mechanism — find a copula, split subject from object, reduce each to an
NP head, then carry polarity and quantification as edge properties — parallels, and
in a hosted setting could compose on, several stronger established tools: SVO /
triple extraction as in textacy, spaCy, Stanford CoreNLP OpenIE, and ClausIE;
negation detection as in negspaCy / medspaCy's NegEx; is-a / hypernym detection in
the lineage of Hearst patterns; and quantifier / natural-logic handling as in
Stanford NatLog. Any of those extracts more, from more sentence shapes, than this
~80-line module does.

Keeping it in-house is a deliberate trade. You give up that breadth and recall to
gain zero runtime dependencies, offline operation, no model download or
supply-chain surface, surface cues carried as inspectable DATA
(`artifacts/extraction.json`) rather than trained weights, and a plane one reviewer
can read end to end. For the family's inputs — short definitional / assertoric
provisions — a tailored copula extractor is sufficient, and auditability matters
more than covering every construction.

What is genuinely distinctive is not the extraction but a thin architectural
contract on top of it: `clean_entity` is the single NP-head primitive shared across
planes. The subject a fact is about, the bearer a deontic duty falls on, and the
holder of an epistemic belief are all reduced by the *same* exported function, so an
addressee resolves to the same entity head across planes by construction rather than
by convention. That cross-plane shared-entity-head contract — one addressee
vocabulary, in one place — is the part that is new here; the copula/SPO parsing
beneath it is not.

It lowers an assertion into a typed 5D edge; it does not decide whether the
assertion is true, and it runs no reasoning over the edges it emits — grounding and
composition live on `loomground-solver`. That boundary is the point.
