# Generative AI Agent

This project is a lightweight ChatGPT-style assistant with a web UI. It stores short-term memory per session and can connect to the OpenAI API when you provide an API key.

## Features
- Simple chat UI with session-based memory.
- Offline fallback responses when no API key is configured.
- Pluggable OpenAI client using the Chat Completions API.

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configure
Create a `.env` file (optional) with:
```
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.7
```

## Run
```bash
uvicorn app.main:app --reload
```
Then open `http://localhost:8000`.
