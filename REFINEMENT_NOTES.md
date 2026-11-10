# LODE.ai / Atlas.ai refinement build — 0.10.1-beta

## User experience
- Updated the displayed application build version to 0.10.1-beta.
- Improved page spacing, navigation labels and visual hierarchy while preserving the existing Streamlit workspace and working tools.
- Renamed the technical Vision Evaluation page to **Developer & Evaluation** and kept encoder diagnostics, dataset audit findings and controlled evaluation material in that technical area.
- Replaced the Engineering Adviser raw JSON dataset audit display with a compact structured table in Developer & Evaluation.
- Made independent verification detail expandable by default and replaced generic numerical metric dumps with member-specific headline results.
- Kept provider exception details in a collapsed troubleshooting area.

## Atlas.ai conversational context and reasoning
- Added a compact project-context builder for project name and user-entered design-basis notes.
- Only drawing observations explicitly marked **Verified by engineer** are added to the assistant's project context; pending and rejected model proposals are excluded.
- Preserved role-based recent conversation history and separated project context, retrieved dataset material and the current question in the Groq request.
- Strengthened the system instructions to separate user facts, verified observations, unverified dataset extracts, assumptions and general engineering explanation.
- Tightened missing-input behaviour and prohibited invented clauses, values and compliance claims.

## Knowledge retrieval
- Fixed numeric tokenisation so clause references such as `3.4.4` and numeric values are actually tokenised.
- Added exact clause extraction and strict clause filtering when a clause is explicitly requested.
- Replaced the earlier simplified term-frequency ranking with a BM25-style lexical relevance score and exact-clause boost.
- Added provenance-aware retrieval context including dataset filename, record identifier, code label, clause as recorded and an explicit source-verification warning.
- Added a bounded retrieval-context formatter for the assistant prompt.
- Retrieval scores remain ranking signals, not probabilities, confidence or proof of code applicability.

## Drawing interpretation and review
- Added response-schema validation for vision output.
- Rejects malformed observation structures and invalid bounding boxes; unsupported element types are downgraded to `unknown`.
- Changed model self-assessment from `confidence` to **model certainty**, with backward compatibility for older responses.
- Explicitly labels model certainty as uncalibrated and requires engineer confirmation for labels, values, dimensions and proposed boxes.
- Added duplicate suppression when sending the same proposal to the Engineer Verification register.
- Updated verification register labels to avoid presenting model certainty as engineering confidence.

## Tests and validation
- Added regression tests for numeric clause tokenisation, strict clause filtering, retrieval provenance, zero-result limits, project-context filtering, vision schema validation and project-context prompt separation.
- Python compilation passed for the edited application and Python modules.
- Automated tests: **40 passed**.
- No live Groq inference was run.
- No Streamlit browser smoke test was run in this build environment because Streamlit is not installed here.
- No labelled drawing accuracy benchmark, independent engineering benchmark campaign or complete BS 8110 compliance validation was performed.

## Deferred / unchanged
- Groq integration and configured model selection remain in place; no model fine-tuning or LoRA training was added.
- CLIP remains an optional diagnostic only; no object detector or segmentation model was introduced.
- No new advanced RC design formulas or structural analysis solver were added in this refinement slice.
- BEME remains a future feature and was not implemented.
- Thesis Chapters 4 and 5 were not changed.
- No account system, database, cloud synchronisation or public deployment was added.

## Engineering limitations
The current structural calculation modules remain limited academic prototypes. Retrieval datasets remain research aids and have not been verified clause-by-clause against the complete standard and amendments. Model-generated drawing observations remain proposals. Do not use outputs or drawings for construction without independent checking and approval by a qualified structural engineer.
