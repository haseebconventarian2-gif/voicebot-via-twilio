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

Python Â· FastAPI Â· Azure OpenAI Â· LangChain Â· FAISS

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

## Detailed Code Reference

**Runtime flow:** `Text/audio -> STT -> retrieval -> LLM -> TTS/text -> channel reply`

### Repository map

- `.github/` - supporting package or resources
- `__pycache__/` - supporting package or resources
- `api/` - supporting package or resources
- `bank.json` - project file
- `bankislami.html` - project file
- `bankislami_voice_config.json` - project file
- `faiss_index/` - supporting package or resources
- `fastapi_app.py` - project file
- `index.faiss` - project file
- `index.pkl` - project file
- `main.py` - project file
- `package.json` - project file
- `package-lock.json` - project file
- `rag_pipeline.py` - project file
- `README.md` - project file
- `requirements.txt` - project file
- `vector_database.py` - project file

### Validation checklist

1. Install dependencies in a clean virtual environment.
2. Configure only the environment variables needed by enabled integrations.
3. Start the documented entry point and test its health or root route.
4. Exercise successful and invalid requests.
5. Confirm secrets, private datasets, indexes, and model artifacts are ignored.

### Production checklist

- Use managed secret storage.
- Add authentication, authorization, rate limiting, and request-size limits.
- Add automated tests, structured logs, monitoring, and health checks.
- Pin and audit dependencies.
- Define retention and privacy controls for audio and customer data.

> This README reflects the current codebase. External AI, telephony, and messaging features require their respective accounts, assets, and approvals.

