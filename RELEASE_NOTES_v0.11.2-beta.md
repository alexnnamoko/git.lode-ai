# Atlas.ai v0.11.2-beta — initial harness engineering integration

## Added
- `lode/harness/` package with controller, task schemas, context manager, allowlisted tool router, output safety assessment and audit helpers.
- Harness execution around drawing vision, Engineering Adviser, frame analysis, beam statics, and selected RC beam/slab/column design operations.
- Developer & Evaluation audit viewer and JSON export.
- Regression tests for harness controls and audit redaction.

## Design choices
- Harness runs around existing deterministic tools; it does not replace them.
- The model is not granted arbitrary code or shell execution.
- Only engineer-verified drawing observations are treated as confirmed context.
- Harness completion is not equivalent to engineering verification, code compliance or professional approval.

## Validation
- 65 automated tests passed.
- Python compilation passed.
- BM001–BM006 benchmark runner passed using its documented closed-form and separate NumPy reference methods.
- OpenSees comparison has not yet been executed.
- Live Groq, browser and hosted deployment tests were not performed.

## Limitations
- Audit storage is in-memory for the current Streamlit session only.
- No authentication/role system, durable audit database, task queue, or fully general-purpose agent tool-calling layer is included.
