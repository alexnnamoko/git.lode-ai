# LODE.ai / Atlas.ai — Phase 1 to 3 implementation progress

**Build:** 0.10.0-beta  
**Base:** v0.9.3 refined UX and reasoning build

This update is an initial implementation slice across Phases 1–3. It improves the existing foundations; it does not claim those phases are complete.

## Phase 1 — AI and knowledge system

### Implemented
- Kept the existing 135 design-rule records and 200 Q&A records.
- Extended retrieval with optional clause, member-type and topic metadata filters.
- Retrieval results now carry dataset, record identifier, code label and clause metadata.
- Retrieval score is explicitly labelled as lexical relevance, not calibrated confidence.
- Added a dataset structure audit for record counts, missing identifiers/references/content and duplicate identifiers.
- Atlas context now labels retrieved records as dataset evidence and passes provenance metadata to the model.
- UI exposes the dataset audit and warns that structural auditing does not verify engineering correctness.

### Audit snapshot
- Rules: 135 records; 89 unique clause references; no missing IDs, missing clause references, duplicate IDs or missing primary formula text detected.
- Q&A: 200 records; 126 unique clause references; no missing IDs, missing clause references, duplicate IDs or missing primary answer text detected.

### Not yet implemented
- Semantic/vector embeddings and hybrid vector + lexical retrieval.
- Clause-by-clause comparison against the complete authoritative standard and amendments.
- Verified worked-example corpus and expert-reviewed answer benchmark.
- Fine-tuning/LoRA.

## Phase 2 — Structural design engines

### Implemented in this slice
- Hardened beam and slab effective-depth geometry validation.
- Added explicit calculation-scope warnings to beam, slab and column results.
- Exposed key material properties and provided reinforcement quantities needed by the independent checker.
- Preserved the current supported modules and their limited assumptions.

### Still outstanding
- Doubly reinforced and flanged beams.
- Complete shear, torsion, deflection and crack-control design.
- Two-way slabs and punching shear.
- Slender, eccentric and biaxial columns.
- Foundations and retaining walls.

No new advanced design method was added because its equations, limits, detailing rules and code references must first be transcribed and independently checked against the applicable standard. Avoiding unverified formulas is intentional.

## Phase 3 — LODE Verification Engine

### Implemented
- Added `lode/verification/engine.py` as an independent arithmetic cross-check layer.
- Added checks for selected beam load, moment, shear, flexural intermediate values and provided steel area.
- Added checks for selected one-way slab load, strip moment and provided steel area.
- Added checks for selected column gross area, concrete area and axial-capacity expression.
- Integrated verification status and individual check results into the design UI.
- A deliberately modified beam moment is detected by the verifier in automated tests.

### Interpretation
- `PASS — LIMITED ARITHMETIC CHECKS` means only the listed numerical identities were independently recalculated and matched.
- It is not a BS 8110 compliance certificate, design approval or evidence that omitted checks pass.
- Complete design verification, source validation, independent benchmark calculations and engineer sign-off remain outstanding.

## Validation performed
- Python compilation passed for changed application and engine modules.
- Automated tests: **29 passed**.
- No live Groq request was made.
- No full Streamlit browser smoke test was performed in this build environment.
- No independent structural-engineering benchmark campaign was performed.

## Safety and engineering limitations
The current beam, slab and column modules remain preliminary academic prototypes. Their existing simplified assumptions and omitted limit-state checks remain. Do not use generated results or drawings as construction instructions without independent checking and approval by a qualified structural engineer.

---

## Refinement follow-on — 0.10.1-beta

This follow-on focuses on the assistant experience and safe evidence handling rather than claiming completion of Phases 1–3.

- Project context now includes only drawing observations explicitly marked `Verified by engineer`; pending proposals are excluded.
- Retrieved knowledge context now carries dataset file, record identifier, code label and clause provenance, with explicit warnings that source content and applicability need checking.
- Numeric clause tokenisation was corrected; explicit clause searches now filter to that clause rather than relying only on token overlap.
- Vision response data is schema-checked; malformed boxes are discarded and model self-reported certainty is not presented as calibrated confidence.
- The technical evaluation area is separated from the routine Adviser workflow; result cards and verification details are less code-heavy.
- Regression suite increased from 29 to **40 passing tests**.

This remains a refinement increment. Semantic search, complete standard verification, advanced RC design coverage, full verification, drawing benchmark validation and a live browser/provider test remain outstanding.
