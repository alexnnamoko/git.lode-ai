# Testing and contributing to LODE.ai

1. Create a Python 3.11 virtual environment.
2. Install `requirements.txt`.
3. Run `python -m pytest -q` before submitting a change.
4. Never commit `.env`, Streamlit secrets, API keys, private drawings or identifiable project data.
5. Include a reproducible test case for changes to extraction, model prompts, calculations or report generation.
6. Do not describe an AI interpretation as verified engineering data until it has been checked against labelled ground truth by a reviewer.
7. Changes to calculation methods must include the governing assumptions, units, code reference and independently checked benchmark examples.

Please report model errors with the model ID, prompt, anonymised input, raw response and reviewer correction where disclosure is permitted.
