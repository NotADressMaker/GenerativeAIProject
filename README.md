# AgentScript Language Studio

AgentScript Language Studio turns the project into a programming language workbench for building
generative AI agents. It provides a chat-based IDE to sketch AgentScript programs, reason
about agent architectures, and iterate on orchestration strategies.

## Features
- Chat-based AgentScript editor with session-based memory.
- Offline fallback guidance for drafting agent programs without an API key.
- Pluggable OpenAI client using the Chat Completions API for language execution assistance.

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

To aggregate multiple model responses and synthesize a final answer, add:
```
OPENAI_MULTI_MODELS=gpt-4o-mini,gpt-4o
OPENAI_SYNTHESIS_MODEL=gpt-4o-mini
```
When `OPENAI_MULTI_MODELS` is set, each listed model will respond and the synthesis model will
combine them into one response.

## Run
```bash
uvicorn app.main:app --reload
```
Then open `http://localhost:8000`.
