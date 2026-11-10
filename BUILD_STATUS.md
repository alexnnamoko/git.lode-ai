# Build status — LODE.ai / Atlas.ai

**Build:** 0.10.2-beta — interface safety and controlled prototype test preparation

## Included
- Groq-hosted Atlas text and vision integration retained.
- Improved project/session context: project notes and only engineer-verified drawing observations are supplied as project context.
- Role-preserving recent chat history retained and clearly separated from retrieved research material.
- Stronger instructions for missing design inputs, source attribution, uncertainty, general engineering explanation and engineer review.
- Corrected numeric clause tokenisation and added strict explicit-clause retrieval, BM25-style lexical ranking and source provenance.
- Added a bounded retrieval-context formatter that labels the bundled knowledge as unverified research-dataset material.
- Added drawing response schema validation, bounding-box validation, model-certainty disclaimers and duplicate suppression in engineer review handoff.
- Polished the Streamlit navigation and calculation result presentation; moved technical dataset audit and CLIP diagnostics into Developer & Evaluation.
- Replaced direct exception text in normal workflows with plain-language feedback; retained session-scoped technical diagnostics in Developer & Evaluation.
- Removed the raw exception `st.code()` display from the Engineering Adviser.
- Added the Prototype 0.1 Scope & Operating Parameters document (Markdown and PDF).
- Existing preliminary beam, one-way slab and short axial column modules and selected arithmetic verification checks preserved.

## Validation
- Python compilation passed for the edited application and modules.
- Automated tests: **43 passed** (including UI safety source checks).
- No live Groq API call was made.
- No full Streamlit browser smoke test was performed; Streamlit is not installed in the build environment.
- No live Groq inference or Tesseract drawing benchmark was performed.
- No labelled drawing-interpretation benchmark, independent structural benchmark campaign or full BS 8110 compliance validation was performed.

## Limitations
- Retrieval remains lexical; semantic/vector retrieval is not yet implemented.
- Knowledge datasets remain research aids, not a complete executable or certified BS 8110 implementation.
- Beam, slab and column design capabilities remain limited and omit important checks and design cases.
- The verification layer checks selected arithmetic only; it does not certify code compliance or structural safety.
- Model-generated drawing content and bounding boxes require engineer verification.
- BEME, thesis Chapters 4 and 5, fine-tuning/LoRA, database/accounts and public deployment remain out of scope for this build.
