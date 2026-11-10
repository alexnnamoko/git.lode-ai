# Atlas.ai model and component card

## Intended use
Academic experimentation with multimodal drawing interpretation, BS 8110 knowledge retrieval and limited reinforced-concrete calculation workflows.

## Components
- Hosted multimodal model: Qwen vision through Groq; default model ID `qwen/qwen3.8-27b`. Confirm current availability and access in the Groq Console.
- Drawing-image path: images are sent to Groq using its vision-capable chat API and processed by the selected hosted model. Provider data terms and current model access should be reviewed before uploading confidential drawings.
- Explicit image encoder: OpenAI CLIP ViT-B/32 (`openai/clip-vit-base-patch32`), optional local CPU diagnostics. CLIP is a separate diagnostic encoder; embeddings are not fused into Qwen prompts in this prototype.
- OCR: Tesseract 5.x through `pytesseract`.
- Image preprocessing: OpenCV grayscale conversion, denoising and adaptive thresholding.
- Retrieval: local JSON records for BS 8110 beam design knowledge, ranked lexically with explicit clause matching and source provenance. The records remain unverified research extracts.
- Numerical processing: deterministic Python modules for a narrow set of beam, slab and column cases.

## Data and provenance
The app includes the supplied BS 8110 beam design Q&A dataset and structured beam-rule dataset. These are retrieval aids. The package does not fine-tune Groq-hosted Qwen vision model or CLIP.

## Limitations
- Groq-hosted Qwen vision model may misread small text, dimensions, symbols, linework, overlapping annotations and drawing conventions.
- OCR can misread characters and symbols; OCR confidence is not engineering confidence.
- CLIP similarity scores are relative, uncalibrated and not object-detection probabilities.
- Model-proposed bounding boxes are approximate and are schema-checked for valid normalised coordinates before display. This does not validate their visual accuracy.
- Model-reported certainty is qualitative self-assessment, not calibrated confidence.
- Atlas session context may include user-entered project notes and only drawing observations explicitly marked “Verified by engineer”; pending proposals are excluded.
- A model response is not a verified drawing interpretation or structural design.
- Calculation modules have narrow stated scopes and do not constitute a complete BS 8110 implementation.

## Human oversight
All drawing observations must pass through the Engineer Verification workflow. Design calculations and code references require independent review against the complete applicable standards, project-specific design basis and professional judgement.

## Evaluation recommendation
Use a separate held-out drawing set with human-labelled text, element classes, dimensions and bounding boxes. Report OCR CER/WER, exact dimension accuracy, object precision/recall/F1, bounding-box IoU, unsupported-claim rate, abstention rate and repeatability. Do not claim accuracy before measuring it.

## Access and cost
A Groq API key is required. Free-tier access and rate limits may be available, but are controlled by the provider and may change. A public Streamlit deployment uses the app owner’s server-side key and quota unless separate per-user authentication and billing are implemented.
