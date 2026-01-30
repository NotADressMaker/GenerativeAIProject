const chatEl = document.getElementById("chat");
const composer = document.getElementById("composer");
const messageInput = document.getElementById("message");
const statusEl = document.getElementById("status");

const sessionIdKey = "agent.sessionId";

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

appendMessage(
  "assistant",
  "Hi! I'm your generative AI agent. Ask me anything and I'll help out."
);

composer.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = messageInput.value.trim();
  if (!message) return;

  appendMessage("user", message);
  messageInput.value = "";
  composer.querySelector("button").disabled = true;

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
    composer.querySelector("button").disabled = false;
  }
});
