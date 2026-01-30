const chatEl = document.getElementById("chat");
const composer = document.getElementById("composer");
const messageInput = document.getElementById("message");
const statusEl = document.getElementById("status");
const resetButton = document.getElementById("reset");

const sessionIdKey = "agent.sessionId";

function appendMessage(role, content) {
  const bubble = document.createElement("div");
  bubble.className = `message ${role}`;
  bubble.textContent = content;
  chatEl.appendChild(bubble);
  chatEl.scrollTop = chatEl.scrollHeight;
  return bubble;
}

function setStatus(text, active) {
  statusEl.textContent = text;
  statusEl.style.background = active ? "#d1fae5" : "#fef2c0";
  statusEl.style.color = active ? "#065f46" : "#7a5b00";
}

async function refreshStatus() {
  try {
    const response = await fetch("/status");
    const data = await response.json();
    setStatus(data.mode === "online" ? "Connected" : "Offline mode", data.mode === "online");
  } catch (error) {
    setStatus("Offline mode", false);
  }
}

appendMessage(
  "assistant",
  "Hi! I'm your generative AI agent. Ask me anything and I'll help out."
);
refreshStatus();

composer.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = messageInput.value.trim();
  if (!message) return;

  appendMessage("user", message);
  messageInput.value = "";
  composer.querySelector("button").disabled = true;
  const typingBubble = appendMessage("typing", "Thinking...");

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
    const data = await response.json();
    if (data.session_id) {
      localStorage.setItem(sessionIdKey, data.session_id);
    }
    typingBubble.remove();
    appendMessage("assistant", data.reply);
    setStatus(data.mode === "online" ? "Connected" : "Offline mode", data.mode === "online");
  } catch (error) {
    typingBubble.remove();
    appendMessage(
      "assistant",
      "Something went wrong. Please try again or check the server logs."
    );
    setStatus("Offline mode", false);
  } finally {
    composer.querySelector("button").disabled = false;
  }
});

resetButton.addEventListener("click", async () => {
  const sessionId = localStorage.getItem(sessionIdKey);
  const formData = new FormData();
  if (sessionId) {
    formData.append("session_id", sessionId);
  }
  try {
    await fetch("/reset", { method: "POST", body: formData });
    chatEl.innerHTML = "";
    appendMessage(
      "assistant",
      "Chat cleared. What would you like to talk about next?"
    );
  } catch (error) {
    appendMessage(
      "assistant",
      "I couldn't clear the chat. Please try again."
    );
  }
});
