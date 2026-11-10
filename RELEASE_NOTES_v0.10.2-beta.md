# Release notes — v0.10.2-beta

## Focus
Preserve the v0.10.1 implementation while reducing exposure of raw implementation details in normal user-facing workflows and preparing a controlled prototype test package.

## Changes
- Updated the displayed build identifier to `0.10.2-beta`.
- Added a central error-reporting helper that presents a concise user-facing message while retaining exception type/details in session-scoped Developer & Evaluation diagnostics.
- Removed the raw exception `st.code()` display from Engineering Adviser troubleshooting.
- Replaced direct exception-string display in application workflows with plain-language error feedback.
- Added a Developer & Evaluation diagnostics panel and a session-level clear action.
- Added `LODE_AI_PROTOTYPE_0.1_SCOPE_AND_OPERATING_PARAMETERS.md`, defining the intended use, capabilities, required inputs, knowledge/drawing boundaries, exclusions, data handling and test-release conditions.

## Preserved
- Groq integration and configured model mechanism.
- Tesseract OCR and vision workflow.
- Existing retrieval, calculation, analysis, verification, detailing, export and report modules.
- Existing datasets and regression tests.

## Validation actually performed in this build environment
- `python -m compileall -q app.py lode tests` — passed.
- `python -m pytest -q` — 40 passed.
- Static scan of `app.py` for `st.code`, `st.exception` and direct exception-string rendering — no matches after edits.
- Full Streamlit browser smoke test — not performed; Streamlit is not installed in the build environment.
- Live Groq inference — not performed.
- Live Tesseract OCR benchmark — not performed.
- Independent structural/code-compliance benchmark — not performed.

## Release status
This is a controlled prototype candidate, not a production-certified or construction-ready application. Complete local browser testing and deployment security checks before inviting external testers.
