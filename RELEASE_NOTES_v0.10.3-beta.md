# Release notes — v0.10.3-beta

## Focus
Clean the tester-facing Overview dashboard and remove environment/developer diagnostics from the persistent sidebar.

## Changes
- Removed API-key detection, Tesseract engine status, optional CLIP diagnostics, connection-test output and build identifier from the Overview page.
- Removed API-key readiness, service implementation labels and build number from the persistent sidebar.
- Replaced the technical system-status panel with a user-oriented workflow and getting-started guide.
- Kept the dedicated Developer & Evaluation workspace and session-scoped diagnostic capture intact.
- Preserved engineering workflows, model integration, drawing interpretation, calculations, verification and exports.

## Validation
Automated test results are recorded separately after running the package test suite in the target Python environment. Live Groq inference, hosted deployment and browser testing are not claimed by this source cleanup.

## Release status
Academic research prototype only. Not for construction or professional engineering approval.
