from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List
from urllib import request
from urllib.error import HTTPError, URLError

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
    max_messages: int
    messages: List[ChatMessage] = field(default_factory=list)

    def add(self, role: str, content: str) -> None:
        self.messages.append(ChatMessage(role=role, content=content))
        self._trim_messages()

    def _trim_messages(self) -> None:
        if self.max_messages <= 0 or len(self.messages) <= self.max_messages:
            return
        system_message = None
        start_idx = 0
        if self.messages and self.messages[0].role == "system":
            system_message = self.messages[0]
            start_idx = 1
        remaining = self.messages[start_idx:]
        keep_count = self.max_messages - (1 if system_message else 0)
        if keep_count <= 0:
            self.messages = [system_message] if system_message else []
            return
        self.messages = ([system_message] if system_message else []) + remaining[-keep_count:]


class ChatMemoryStore:
    def __init__(self, max_messages: int) -> None:
        self._sessions: Dict[str, ChatSession] = {}
        self._max_messages = max_messages

    def get_or_create(self, session_id: str | None) -> ChatSession:
        if not session_id:
            session_id = uuid.uuid4().hex
        if session_id not in self._sessions:
            self._sessions[session_id] = ChatSession(
                session_id=session_id,
                max_messages=self._max_messages,
            )
        return self._sessions[session_id]


class OpenAIChatError(RuntimeError):
    pass


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
        try:
            with request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError) as exc:
            raise OpenAIChatError("OpenAI request failed") from exc
        if "error" in body:
            raise OpenAIChatError(body["error"].get("message", "OpenAI error response"))
        return body["choices"][0]["message"]["content"]


class MultiModelChatClient:
    def __init__(
        self,
        api_key: str,
        models: List[str],
        temperature: float,
        synthesis_model: str | None,
    ) -> None:
        self.clients = [OpenAIChatClient(api_key, model, temperature) for model in models]
        self.model_names = models
        self.synthesis_client = OpenAIChatClient(
            api_key,
            synthesis_model or models[0],
            temperature,
        )

    @staticmethod
    def _format_transcript(messages: List[ChatMessage]) -> str:
        lines = []
        for message in messages:
            role = message.role.capitalize()
            lines.append(f"{role}: {message.content}")
        return "\n".join(lines)

    def generate(self, messages: List[ChatMessage]) -> str:
        model_outputs = []
        for model_name, client in zip(self.model_names, self.clients):
            response = client.generate(messages)
            model_outputs.append((model_name, response))

        transcript = self._format_transcript(messages)
        synthesis_prompt = (
            "You are an expert AI orchestrator. Combine the model responses into a single, "
            "clear, and accurate answer. Preserve important details, resolve conflicts, and "
            "avoid mentioning that multiple models were used."
        )
        synthesis_messages = [
            ChatMessage(role="system", content=synthesis_prompt),
            ChatMessage(
                role="user",
                content=(
                    f"Conversation so far:\n{transcript}\n\n"
                    "Model responses:\n"
                    + "\n\n".join(
                        f"{model_name}:\n{response}"
                        for model_name, response in model_outputs
                    )
                    + "\n\nProvide the best possible final response."
                ),
            ),
        ]
        return self.synthesis_client.generate(synthesis_messages)


class FallbackChatClient:
    def generate(self, messages: List[ChatMessage]) -> str:
        last_user = next((m for m in reversed(messages) if m.role == "user"), None)
        if not last_user:
            return (
                "Ask me about the AgentScript language and I'll help you design an agent."
            )
        return (
            "I'm running in offline mode. "
            "Set OPENAI_API_KEY to connect to the OpenAI API. "
            "I'll still help you sketch AgentScript programs here. "
            f"You said: {last_user.content}"
        )


class ChatAgent:
    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        multi_models = [
            item.strip()
            for item in os.getenv("OPENAI_MULTI_MODELS", "").split(",")
            if item.strip()
        ]
        synthesis_model = os.getenv("OPENAI_SYNTHESIS_MODEL", "").strip() or None
        temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
        self.fallback_client = FallbackChatClient()
        if api_key:
            if multi_models:
                models = multi_models if multi_models else [model]
                self.client = MultiModelChatClient(
                    api_key,
                    models,
                    temperature,
                    synthesis_model,
                )
            else:
                self.client = OpenAIChatClient(api_key, model, temperature)
        else:
            self.client = self.fallback_client

    def respond(self, session: ChatSession, user_message: str) -> tuple[str, str]:
        system_prompt = (
            "You are the AgentScript language guide and compiler. "
            "Help users build generative AI agents by explaining syntax, "
            "program structure, and best practices. Provide concise examples, "
            "suggest improvements, and ask clarifying questions when needed."
        )
        if not session.messages or session.messages[0].role != "system":
            session.messages.insert(0, ChatMessage(role="system", content=system_prompt))
        session.add("user", user_message)
        try:
            reply = self.client.generate(session.messages)
            mode = "offline" if self.client is self.fallback_client else "openai"
        except OpenAIChatError:
            reply = self.fallback_client.generate(session.messages)
            mode = "offline"
        session.add("assistant", reply)
        return reply, mode


app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")
max_messages = int(os.getenv("CHAT_MAX_MESSAGES", "20"))
store = ChatMemoryStore(max_messages=max_messages)
agent = ChatAgent()


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/chat")
def chat(message: str = Form(...), session_id: str | None = Form(None)) -> JSONResponse:
    session = store.get_or_create(session_id)
    reply, mode = agent.respond(session, message)
    return JSONResponse(
        {"session_id": session.session_id, "reply": reply, "mode": mode}
    )
