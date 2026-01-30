# Generative AI Agent

This project is a lightweight ChatGPT-style assistant with a web UI. It stores short-term memory per session and can connect to the OpenAI API when you provide an API key.

## Features
- Simple chat UI with session-based memory.
- Offline fallback responses when no API key is configured.
- Pluggable OpenAI client using the Chat Completions API.
- Status + reset endpoints for checking connectivity and clearing chats.

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
OPENAI_TIMEOUT=30
CHAT_HISTORY_LIMIT=16
SYSTEM_PROMPT=You are a helpful, friendly AI assistant.
```

## Run
```bash
uvicorn app.main:app --reload
```
Then open `http://localhost:8000`.

## Endpoints
- `POST /chat` accepts `message` and optional `session_id`.
- `GET /status` reports whether the server is in online/offline mode.
- `POST /reset` clears the current session's chat history.
