from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List
from urllib import request

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

load_dotenv()

@dataclass
class ChatMessage:
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class ChatSession:
    session_id: str
    messages: List[ChatMessage] = field(default_factory=list)

    def add(self, role: str, content: str) -> None:
        self.messages.append(ChatMessage(role=role, content=content))


class ChatMemoryStore:
    def __init__(self) -> None:
        self._sessions: Dict[str, ChatSession] = {}

    def get_or_create(self, session_id: str | None) -> ChatSession:
        if not session_id:
            session_id = uuid.uuid4().hex
        if session_id not in self._sessions:
            self._sessions[session_id] = ChatSession(session_id=session_id)
        return self._sessions[session_id]


class OpenAIChatClient:
    def __init__(self, api_key: str, model: str, temperature: float) -> None:
        self.api_key = api_key
        self.model = model
        self.temperature = temperature

    def generate(self, messages: List[ChatMessage]) -> str:
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        with request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"]


class FallbackChatClient:
    def generate(self, messages: List[ChatMessage]) -> str:
        last_user = next((m for m in reversed(messages) if m.role == "user"), None)
        if not last_user:
            return "Tell me what you'd like help with, and I'll do my best to assist."
        return (
            "I'm running in offline mode. "
            "Set OPENAI_API_KEY to connect to the OpenAI API. "
            f"You said: {last_user.content}"
        )


class ChatAgent:
    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
        if api_key:
            self.client: Any = OpenAIChatClient(api_key, model, temperature)
        else:
            self.client = FallbackChatClient()

    def respond(self, session: ChatSession, user_message: str) -> str:
        system_prompt = (
            "You are a helpful, friendly AI assistant. "
            "Answer clearly and concisely, and ask follow-up questions when helpful."
        )
        if not session.messages or session.messages[0].role != "system":
            session.messages.insert(0, ChatMessage(role="system", content=system_prompt))
        session.add("user", user_message)
        reply = self.client.generate(session.messages)
        session.add("assistant", reply)
        return reply


app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")
store = ChatMemoryStore()
agent = ChatAgent()


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/chat")
def chat(message: str = Form(...), session_id: str | None = Form(None)) -> JSONResponse:
    session = store.get_or_create(session_id)
    reply = agent.respond(session, message)
    return JSONResponse({"session_id": session.session_id, "reply": reply})
