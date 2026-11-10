# LODE.ai / Atlas.ai — Groq-hosted multimodal build

**Current refinement package:** 0.10.2-beta

Academic research prototype for exploring a multimodal engineering assistant for reinforced-concrete design. **Not for construction or independent engineering approval.**


## Prototype 0.1 scope and operating parameters

See `LODE_ai_Prototype_0.1_Scope_and_Operating_Parameters.pdf` (and the matching Markdown file) before conducting a test session. It defines intended use, supported workflows, input responsibilities, retrieval and drawing limitations, explicit exclusions, data handling precautions and pre-test conditions.

## What this build uses

- **Groq API** to host and run the AI model online. The app uses the Groq Python SDK and the Chat Completions API.
- **Qwen vision model** (`qwen/qwen3.8-27b`) for text questions and image-input drawing interpretation, subject to the model's current availability and account limits on Groq.
- **Tesseract OCR** for extracting printed text from drawing images and rendered PDF pages.
- **CLIP ViT-B/32** as an optional, separate image/text embedding evaluation tool. CLIP embeddings are not fused into the Groq model input.
- Supplied BS 8110 Q&A and beam-rule JSON datasets for retrieval context. These are reference aids, not a complete executable code implementation.

The model is hosted by Groq. Your computer does not download or run the large Qwen model. The application sends text and, when you request drawing interpretation, the selected image to Groq for inference. Do not upload confidential client drawings unless you have permission and have reviewed the provider's current data terms.

## Requirements

- Windows 10/11 or another supported Python environment.
- Python 3.11 recommended.
- Internet connection.
- A Groq account and API key. Free-tier access may be available, subject to model availability, rate limits and usage policies. Higher usage may require paid billing.
- Tesseract OCR installed separately for local Windows use. The Python `pytesseract` package alone does not install the Tesseract executable.

## Windows setup

1. Extract the ZIP to a normal folder, for example `C:\\LODE_ai`.
2. Install Python 3.11 if it is not already installed. Enable the Python Launcher during installation.
3. Run `setup_windows.bat`. It creates `.venv` and installs the Python dependencies, including the Groq SDK.
4. Create a Groq API key from the [Groq Console](https://console.groq.com/keys).
5. Copy `.env.example` to a new file named `.env` in the project root.
6. Open `.env` in Notepad and replace the placeholder with your key:

   ```dotenv
   GROQ_API_KEY=your_actual_groq_api_key
   LODE_MODEL=qwen/qwen3.8-27b
   ```

7. Install Tesseract separately if needed. Windows installer instructions are in the [UB Mannheim Tesseract guide](https://github.com/UB-Mannheim/tesseract/wiki).
8. Run `run_lode.bat`.
9. In the app, open **Overview** and click **Test Groq API connection**.
10. Once the connection test succeeds, open **Engineering Adviser** and ask a simple question. Set your project description in **Projects** if you want Atlas to use it as session context. Then test **Drawing Studio** separately if you want to try image interpretation. Model-proposed drawing observations are not added to Atlas project context unless an engineer explicitly marks them as verified.

## Deploying the app online

1. Push the extracted project folder contents to a GitHub repository. Do not upload `.env`.
2. Create a Streamlit Community Cloud app from that repository, with `app.py` as the entry point.
3. In the Streamlit app settings, add this under **Secrets**:

   ```toml
   GROQ_API_KEY = "your_actual_groq_api_key"
   LODE_MODEL = "qwen/qwen3.8-27b"
   ```

4. Deploy/reboot the app. The application reads the secret server-side. Never put the API key in browser code, public source files, screenshots or commits.
5. Check the Groq console for model access and usage limits. If the selected model is unavailable to your account or has been renamed/retired, choose a currently available vision-capable model and update the `LODE_MODEL` environment setting and restart the app.

**Important:** Streamlit hosts the LODE.ai user interface; Groq hosts the AI inference. GitHub stores source code; it does not host the model. Keep the Groq key private. A single shared Groq key means requests from all app visitors consume the owner's Groq quota, so a public release will need usage controls, authentication and abuse protection before broad distribution.

## Tesseract and AI are different stages

- Tesseract extracts text from a drawing.
- Groq's vision model interprets the image and can compare visual content with OCR text.
- OCR output and model interpretations remain unverified until reviewed by an engineer.

## Optional CLIP evaluation

Install the optional packages only if you want to use the separate Developer & Evaluation page:

```powershell
pip install -r requirements-vision.txt
```

The first run may download model weights. CLIP similarity scores are not calibrated probabilities or proof of drawing-recognition accuracy.

## Engineering limitations

This package is an academic prototype. The structural modules are limited, and the supplied BS 8110 datasets are retrieval aids. Model responses can be wrong, incomplete or misleading. Do not use outputs for construction or professional approval. Independently verify all inputs, calculations, clauses, assumptions and detailing against the complete applicable standards and qualified engineering review.

## Troubleshooting

- **`GROQ_API_KEY is missing`:** Check the `.env` filename and key spelling, then restart the app. On Streamlit Cloud, add the key under app Secrets and reboot.
- **401 / authentication error:** Create a fresh key in the Groq Console and replace the old one. Do not paste the key into chat or GitHub.
- **429 / rate limit:** Wait for the limit to reset or review your account's current rate limits and usage plan.
- **Model not found / access denied:** Check the current Groq model catalogue and confirm that your account can access the model ID configured in `LODE_MODEL`.
- **Drawing vision request fails:** Check image file size and format, then test with a smaller PNG/JPEG. Groq's vision documentation lists current image limits.
- **Tesseract not detected:** Install the Tesseract executable separately and set `TESSERACT_CMD` in `.env` to its full path if it is not on PATH.
