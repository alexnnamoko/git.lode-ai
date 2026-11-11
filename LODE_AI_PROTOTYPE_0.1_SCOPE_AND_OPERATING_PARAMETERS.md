# LODE.ai / Atlas.ai — Prototype 0.1 Scope & Operating Parameters

**Release candidate:** v0.10.2-beta  
**Product:** LODE.ai engineering workspace  
**Assistant:** Atlas.ai  
**Intended audience:** invited civil/structural engineering testers and academic reviewers  
**Status:** controlled prototype test release; not approved for professional design or construction use.

## 1. Purpose

LODE.ai Prototype 0.1 is an academic research prototype exploring a multimodal assistant for reinforced-concrete (RC) engineering workflows. Atlas.ai combines a hosted language/vision model, local drawing-text extraction, retrieval from supplied BS 8110 research datasets, selected preliminary calculation modules, and an engineer-review workflow.

The prototype is intended to gather structured feedback on usability, retrieval relevance, conversational assistance, drawing-observation quality and selected calculation workflows. It is not a certified design package, a replacement for a structural engineer, or an executable implementation of the complete BS 8110 standard.

## 2. Intended operating domain

- **Primary engineering domain:** preliminary reinforced-concrete building design assistance.
- **Primary reference basis:** supplied BS 8110-related Q&A and beam-design-rule JSON datasets.
- **Assistant provider:** Groq-hosted model endpoint configured through `GROQ_API_KEY` and `LODE_MODEL`.
- **Drawing text extraction:** Tesseract OCR, where the Tesseract executable is installed and available.
- **Application:** Python / Streamlit browser interface.
- **Project state:** current Streamlit session; no persistent multi-user project database is included.

The configured model identifier is an environment setting, not a guarantee that a particular model remains available. The operator must confirm current provider access before a test session.

## 3. Functional capabilities included

### 3.1 Atlas.ai engineering adviser
- Accepts natural-language questions about structural engineering and RC design.
- Uses recent conversation history within the active session.
- Uses project name and design-basis notes supplied by the user.
- Uses drawing observations only after an engineer marks them as verified in the review workflow.
- Retrieves potentially relevant records from the bundled knowledge datasets and can expose the retrieved record references.
- Can explain general engineering concepts and preliminary methods, subject to model limitations and source availability.

### 3.2 Drawing Studio
- Accepts PDF and common raster drawing formats supported by the interface.
- Extracts embedded PDF text where available.
- Runs Tesseract OCR on the selected page/image when configured.
- Sends the selected drawing image and OCR text to the configured vision model when requested.
- Presents model-proposed observations and approximate regions for review.
- Does not automatically treat model proposals as verified engineering inputs.

### 3.3 Engineer Verification
- Allows a reviewer to edit, classify and confirm or reject drawing observations.
- Only observations marked `Verified by engineer` are eligible for inclusion in Atlas project context.
- The application does not independently authenticate the reviewer or certify the correctness of a confirmation.

### 3.4 Structural modelling, analysis and preliminary design modules
- Manual generation of a regular planar multi-bay, multi-storey 2D frame from user-entered geometry.
- Explicit beam and column placement/connectivity at generated grid nodes, with user-entered rectangular gross section dimensions and elastic modulus.
- Fixed-base support idealisation and a linear-elastic 2D Euler-Bernoulli frame solver using the direct stiffness method.
- Applied nodal horizontal/vertical forces and nodal moments; reported joint displacements, support reactions and member local end actions.
- Simply supported beam statics for full-span uniformly distributed load and downward point loads.
- Limited preliminary rectangular RC beam design for the implemented simply supported/UDL case.
- Limited preliminary one-way slab design using a one-metre design strip and simply supported assumptions.
- Limited short tied rectangular column calculation for concentric axial compression, with user confirmation of the short-column/axial-only assumptions.
- Preliminary beam reinforcement bar selection/schedule from a supplied required steel area.
- Selected independent arithmetic checks and equilibrium residual checks.

The 2D frame solver is a research implementation for regular planar frames. It assumes prismatic members, rigid joints, gross section properties, small displacements and first-order linear-elastic behaviour. Only nodal loads are currently supported; member distributed loads, end releases, 3D behaviour, shear deformation, P-Delta effects, buckling and dynamic analysis are not implemented. The solver is not independently validated for professional use. The precise calculation assumptions and limitations shown in each module must be read before interpreting its result. A passed arithmetic check is not a code-compliance check.

### 3.5 Reports and project handling
- Session-level project metadata and evidence.
- JSON project-session export/import.
- CSV verification-register export.
- PDF project report export.
- Developer diagnostics separated from ordinary workflows.

## 4. Required inputs and user responsibilities

The user/tester is responsible for supplying and checking:
- Correct project description, design basis, units and applicable design standard/edition.
- Geometry, spans, support conditions, load cases and combinations.
- Concrete and reinforcement properties, cover, member dimensions and all other module inputs.
- Drawing scale, page selection, image legibility and the interpretation of extracted labels/dimensions.
- Whether the assumptions of a selected calculation module actually apply to the real structure.

Atlas.ai must be treated as an assistant for exploration and explanation. If key inputs are missing, ambiguous or contradictory, the response should request clarification or state the limitation rather than silently inventing values.

## 5. Knowledge and citation parameters

- Retrieval searches the bundled JSON datasets; it does not query or validate the complete published BS 8110 text automatically.
- Retrieved entries are research-dataset records. Their presence does not prove that the wording, numerical value, clause reference, amendment status or applicability is correct.
- The user must verify any quoted clause, factor, limit, equation or design requirement against an authorised copy of the complete applicable standard and amendments.
- If no relevant record is retrieved, Atlas should say that no matching dataset record was found and must not fabricate a clause reference.
- General engineering explanations must be distinguished from statements attributed to a BS 8110 dataset record.

## 6. Drawing interpretation parameters

- OCR output is text recognition, not structural interpretation.
- Vision output is a model proposal, not ground truth.
- Model-reported certainty is qualitative and uncalibrated; it is not a probability of correctness.
- Bounding boxes are approximate model proposals and have not been established as measurement-grade geometry.
- Dimensions, reinforcement marks, member labels, grids and element classifications require comparison with the original drawing and engineer confirmation.
- Drawing uploads do not automatically generate or verify the structural model. The new manually generated 2D frame model is a limited linear-elastic analysis model, not a full building, 3D, second-order or certified finite-element analysis.

## 7. Explicit exclusions

The prototype does not claim to provide:
- Complete or certified BS 8110 compliance checking.
- Full 3D/global building analysis, second-order analysis, load-path analysis or automatic structural modelling from drawings. The limited manually defined planar 2D frame solver is not a substitute for these capabilities.
- Full continuous, doubly reinforced or flanged beam design; comprehensive torsion, shear, deflection and crack-width checks.
- Full two-way slab, punching shear, foundation, retaining-wall, slender-column or biaxial-column design.
- Construction-ready reinforcement detailing, anchorage/lap/curtailment validation, bar bending schedules certified for construction, or production DXF drawings.
- Steel design, BEME/BOQ automation, model fine-tuning/LoRA, user accounts, role-based access control, persistent cloud database or multi-user synchronisation.
- Signed engineering approval, professional certification or construction suitability.

## 8. Data handling and deployment precautions

- Text and selected drawing images are sent to the configured Groq-hosted inference endpoint when the relevant AI action is used.
- Do not submit confidential, personal, security-sensitive or client-restricted drawings unless the owner has authorised the processing and the tester has reviewed applicable provider terms and organisational policies.
- Keep `GROQ_API_KEY` in local environment configuration or the deployment platform's server-side secrets. Never commit it to source control or expose it in the browser.
- A shared deployment using one provider key may consume the owner's quota and incur usage costs. Broad public access requires authentication, rate/usage controls, abuse prevention, monitoring and an appropriate privacy notice before release.
- The app's current session-based project state is not a durable record system. Export important test records and store them securely outside the app.

## 9. Test-release conditions

Before inviting external testers, the operator should:
1. Install dependencies in a clean supported Python environment and run the automated test suite.
2. Run the Streamlit app locally and smoke-test every visible page and principal workflow.
3. Verify Groq credentials and the configured model using a live connection test.
4. Verify Tesseract installation and test OCR on representative drawings.
5. Confirm that raw source code, tracebacks, secrets and implementation payloads are not exposed in ordinary user workflows.
6. Use non-confidential sample drawings and independently checked calculation examples.
7. Explain the prototype limitations to every tester and collect feedback without treating output as approved design.

A successful software test or live model response does not demonstrate engineering accuracy. Calculation and drawing accuracy require separately designed benchmark sets with ground truth and independent engineering review.

## 10. Recommended tester evaluation areas

| Evaluation area | Suggested observations |
|---|---|
| Usability | Navigation clarity, labels, feedback, error recovery and task completion time |
| Conversation | Context retention, follow-up understanding, missing-input questions and clarity |
| Knowledge retrieval | Relevance, exact source traceability, false matches and unsupported questions |
| Drawing OCR | Exact text accuracy, dimension transcription errors and missed annotations |
| Vision interpretation | Element-label accuracy, classification errors, uncertainty handling and box overlap against labelled references |
| Calculation modules | Input validation, reproducibility and agreement with independently checked examples |
| Reliability | Crashes, timeouts, provider failures, session loss and diagnostic usefulness |

## 11. Release statement

LODE.ai Prototype 0.1 is suitable only for controlled evaluation within the capabilities and limitations stated in this document. It is not approved for construction, tender, statutory submission or independent professional design. Every engineering input, assumption, retrieved provision, calculation and drawing interpretation must be independently checked by a qualified structural engineer against the complete applicable standards and project requirements.
