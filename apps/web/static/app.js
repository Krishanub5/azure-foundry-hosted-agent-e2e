const form = document.getElementById("chat-form");
const input = document.getElementById("message-input");
const messages = document.getElementById("messages");
const sendButton = document.getElementById("send-button");
const newChatButton = document.getElementById("new-chat");
const title = document.getElementById("app-title");

let conversationId = window.localStorage.getItem("conversationId");

function appendMessage(role, text, pending = false) {
  const article = document.createElement("article");
  article.className = `message ${role}`;
  const bubble = document.createElement("div");
  bubble.className = `bubble${pending ? " pending" : ""}`;
  bubble.textContent = text;
  article.appendChild(bubble);
  messages.appendChild(article);
  messages.scrollTop = messages.scrollHeight;
  return article;
}

async function loadConfig() {
  try {
    const response = await fetch("/api/config");
    if (response.ok) {
      const config = await response.json();
      title.textContent = config.title;
      document.title = config.title;
    }
  } catch {
    // The static fallback title is sufficient.
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message) return;

  appendMessage("user", message);
  input.value = "";
  input.disabled = true;
  sendButton.disabled = true;
  const pending = appendMessage("assistant", "Thinking…", true);

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
      }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "The request failed");
    }
    conversationId = payload.conversation_id;
    window.localStorage.setItem("conversationId", conversationId);
    pending.querySelector(".bubble").textContent = payload.answer;
    pending.querySelector(".bubble").classList.remove("pending");
  } catch (error) {
    pending.querySelector(".bubble").textContent =
      error.message || "The assistant is temporarily unavailable.";
    pending.querySelector(".bubble").classList.remove("pending");
    pending.classList.add("error");
  } finally {
    input.disabled = false;
    sendButton.disabled = false;
    input.focus();
  }
});

newChatButton.addEventListener("click", () => {
  conversationId = null;
  window.localStorage.removeItem("conversationId");
  messages.replaceChildren();
  appendMessage(
    "assistant",
    "Started a new conversation. What would you like to know?",
  );
  input.focus();
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

loadConfig();
