<div align="center">

# Voice Bot via Twilio

Voice bot prototype using FastAPI, Azure OpenAI chat and speech services, with Twilio integration support.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Status](https://img.shields.io/badge/Status-Reference%20Implementation-6366F1)

</div>

---

## Overview

Voice bot prototype using FastAPI, Azure OpenAI chat and speech services, with Twilio integration support.

## Highlights

- Text conversation endpoint
- Speech-to-text and text-to-speech
- Conversational AI responses
- Twilio integration foundation

## Tech Stack

Python · FastAPI · Azure OpenAI · LangChain · FAISS

## Getting Started

```bash
git clone https://github.com/haseebconventarian2-gif/voicebot-via-twilio.git
cd voicebot-via-twilio
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Configure Azure OpenAI deployments and any messaging-channel credentials in `.env`.

> Store credentials in `.env` and never commit secrets.

## Run

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Project Status

This is a learning and reference implementation. Review security, validation, monitoring, and deployment settings before production use.

<!-- code-audit-details -->

## 🔄 Runtime Flow

`Text/audio → STT → retrieval → Azure chat → TTS/text → messaging channel`

This flow is derived from the current entry points and service calls.

## 🗂 Code Map

| Path | Responsibility |
| --- | --- |
| `.github/` | Supporting resource |
| `__pycache__/` | Supporting resource |
| `api/` | Supporting resource |
| `bank.json` | Supporting resource |
| `bankislami.html` | Supporting resource |
| `bankislami_voice_config.json` | Supporting resource |
| `faiss_index/` | Supporting resource |
| `fastapi_app.py` | Supporting resource |
| `main.py` | Application entry point |
| `package.json` | Node.js dependencies |
| `package-lock.json` | Supporting resource |
| `rag_pipeline.py` | Retrieval and generation pipeline |
| `requirements.txt` | Python dependencies |
| `vector_database.py` | Document indexing and vector storage |

## 🔐 Environment Variables

No environment-variable reads were detected.

## 🌐 Detected API Routes

| Method | Endpoint |
| --- | --- |
| `GET` | `/` |
| `GET` | `/health` |
| `GET` | `/media/{media_id}` |
| `GET` | `/tts` |
| `GET` | `/webhook` |
| `GET` | `/whatsapp/diagnose` |
| `POST` | `/audio` |
| `POST` | `/text` |
| `POST` | `/webhook` |
| `POST` | `/whatsapp/push` |

## 🧪 Validation Guide

1. Install dependencies in a clean virtual environment.
2. Start the documented entry point and test the root or health route.
3. Exercise one valid and one invalid request.
4. Verify external-service errors are handled clearly.
5. Confirm secrets, private data, indexes, and model artifacts are ignored.

## 🔒 Production Checklist

- Use managed secret storage and rotate exposed credentials.
- Add authentication, authorization, rate limiting, and request-size limits.
- Add automated tests, structured logging, monitoring, and health checks.
- Pin and audit dependencies.
- Define retention and privacy controls for audio and customer data.

## ⚠️ Code-Audit Notes

- Documentation reflects the current repository code and may expose integrations that need separate cloud accounts, model assets, or channel approval.
- Treat the project as a reference implementation until its security and deployment configuration are hardened.
