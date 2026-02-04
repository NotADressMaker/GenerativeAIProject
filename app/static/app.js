const chatEl = document.getElementById("chat");
const composer = document.getElementById("composer");
const messageInput = document.getElementById("message");
const statusEl = document.getElementById("status");
const clearButton = document.getElementById("clear-chat");
const hintButtons = document.querySelectorAll("[data-prompt]");

const sessionIdKey = "agent.sessionId";
let isSending = false;

function appendMessage(role, content) {
  const bubble = document.createElement("div");
  bubble.className = `message ${role}`;
  bubble.textContent = content;
  chatEl.appendChild(bubble);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function setStatus(text, active) {
  statusEl.textContent = text;
  statusEl.style.background = active ? "#d1fae5" : "#fef2c0";
  statusEl.style.color = active ? "#065f46" : "#7a5b00";
}

function setComposerState(sending) {
  isSending = sending;
  composer.querySelector("button").disabled = sending;
  messageInput.disabled = sending;
}

function resetChatUI() {
  chatEl.innerHTML = "";
  appendMessage(
    "assistant",
    "Welcome to AgentScript. Tell me the agent you want to build and I'll draft the program."
  );
}

appendMessage(
  "assistant",
  "Welcome to AgentScript. Tell me the agent you want to build and I'll draft the program."
);

composer.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = messageInput.value.trim();
  if (!message) return;

  appendMessage("user", message);
  messageInput.value = "";
  setComposerState(true);

  const sessionId = localStorage.getItem(sessionIdKey);
  const formData = new FormData();
  formData.append("message", message);
  if (sessionId) {
    formData.append("session_id", sessionId);
  }

  try {
    const response = await fetch("/chat", {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      throw new Error("Request failed");
    }
    const data = await response.json();
    if (data.session_id) {
      localStorage.setItem(sessionIdKey, data.session_id);
    }
    appendMessage("assistant", data.reply);
    if (data.mode === "openai") {
      setStatus("Connected", true);
    } else {
      setStatus("Offline mode", false);
    }
  } catch (error) {
    appendMessage(
      "assistant",
      "Something went wrong. Please try again or check the server logs."
    );
    setStatus("Offline mode", false);
  } finally {
    setComposerState(false);
  }
});

messageInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    if (!isSending) {
      composer.requestSubmit();
    }
  }
});

clearButton.addEventListener("click", async () => {
  const sessionId = localStorage.getItem(sessionIdKey);
  if (sessionId) {
    const formData = new FormData();
    formData.append("session_id", sessionId);
    try {
      await fetch("/chat/clear", { method: "POST", body: formData });
    } catch (error) {
      // Ignore errors, still reset UI.
    }
  }
  localStorage.removeItem(sessionIdKey);
  resetChatUI();
  setStatus("Offline mode", false);
});

hintButtons.forEach((button) => {
  button.addEventListener("click", () => {
    messageInput.value = button.dataset.prompt || "";
    messageInput.focus();
  });
});
