/* chatbot.js - improved UI behavior + quick replies
   Expects IDs: #chat-form, #user-input, #chat-box, .chat-panel-wrapper
   Posts to: POST /chat/ask/ { message }
*/

document.addEventListener("DOMContentLoaded", () => {
  const chatForm = document.getElementById("chat-form");
  const userInput = document.getElementById("user-input");
  const chatBox = document.getElementById("chat-box");
  const wrapper = document.querySelector(".chat-panel-wrapper");

  if (!chatForm || !userInput || !chatBox || !wrapper) return;

  // CSRF helper
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
  const csrftoken = getCookie("csrftoken");

  // localStorage draft
  const DRAFT_KEY = "saving_souls_chat_draft_v2";
  userInput.value = localStorage.getItem(DRAFT_KEY) || "";
  userInput.addEventListener("input", () => localStorage.setItem(DRAFT_KEY, userInput.value));

  // helper functions
  function escapeHtml(s) {
    if (s === undefined || s === null) return "";
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#039;");
  }
  function nowTime() {
    const d = new Date(); return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }
  function isNearBottom(threshold = 160) {
    return chatBox.scrollHeight - chatBox.clientHeight - chatBox.scrollTop <= threshold;
  }

  // new message hint (re-attach or create)
  let newHint = document.getElementById("new-message-hint");
  if (!newHint) {
    newHint = document.createElement("div");
    newHint.id = "new-message-hint";
    newHint.textContent = "New messages";
    newHint.style.display = "none";
    wrapper.appendChild(newHint);
  }
  newHint.addEventListener("click", () => { chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: "smooth" }); newHint.style.display = "none"; });

  // DOM builders
  function makeAvatar(role) {
    const el = document.createElement("div");
    el.className = "msg-avatar";
    el.textContent = role === "user" ? "🧑" : "🤖";
    if (role === "user") el.style.background = "linear-gradient(135deg,#6f6ef0,#3db3ff)";
    return el;
  }

  function makePlaceholder() {
    const ph = document.createElement("div");
    ph.className = "avatar-placeholder";
    return ph;
  }

  function createGroup(role) {
    const g = document.createElement("div");
    g.className = "message-group";
    g.dataset.role = role;
    return g;
  }

  function appendMessage({ role = "ai", text = "", time = null, allowGrouping = true }) {
    // grouping logic: try to append to last group if same role
    const last = chatBox.lastElementChild;
    const canGroup = allowGrouping && last && last.dataset && last.dataset.role === role;
    let group = canGroup ? last : createGroup(role);

    if (!canGroup) {
      // insert avatar for new group
      if (role === "ai") group.appendChild(makeAvatar("ai"));
      else group.appendChild(makePlaceholder()); // user messages align right; placeholder keeps layout stable
    } else {
      // add invisible placeholder to keep bubble alignment stable
      group.appendChild(makePlaceholder());
    }

    // bubble
    const bubble = document.createElement("div");
    bubble.className = "bubble " + (role === "user" ? "user-bubble" : "ai-bubble");
    bubble.innerHTML = escapeHtml(text).replace(/\n/g, "<br>");
    group.appendChild(bubble);

    // meta/time
    const meta = document.createElement("div");
    meta.className = "msg-meta";
    meta.textContent = time || nowTime();
    group.appendChild(meta);

    if (!canGroup) chatBox.appendChild(group);

    // scroll or show hint
    if (isNearBottom()) {
      chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: "smooth" });
      newHint.style.display = "none";
    } else {
      newHint.style.display = "block";
    }
  }

  // typing indicator
  function showTyping() {
    const group = createGroup("ai");
    group.appendChild(makeAvatar("ai"));
    const dotWrap = document.createElement("div");
    dotWrap.className = "typing-indicator";
    dotWrap.innerHTML = `<div class="typing-dots" aria-hidden="true"><span></span><span></span><span></span></div>`;
    group.appendChild(dotWrap);
    chatBox.appendChild(group);
    chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: "smooth" });
    return group;
  }

  function removeEl(el) { if (el && el.parentNode) el.parentNode.removeChild(el); }

  // Quick reply chips (inserted above footer)
  function createQuickChips() {
    // only create once
    let chips = wrapper.querySelector(".quick-chips");
    if (chips) return chips;
    chips = document.createElement("div");
    chips.className = "quick-chips";
    const suggestions = ["I feel sad", "I'm anxious", "I had a panic attack", "I'm lonely", "I need help"];
    suggestions.forEach(s => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "quick-chip";
      btn.textContent = s;
      btn.addEventListener("click", () => {
        // fill input and send immediately
        userInput.value = s;
        localStorage.setItem(DRAFT_KEY, s);
        chatForm.requestSubmit();
      });
      chips.appendChild(btn);
    });
    // insert before footer
    const panel = wrapper.querySelector(".chat-panel");
    panel.insertBefore(chips, panel.querySelector(".chat-footer"));
    return chips;
  }

  createQuickChips();

  // submit handling
  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const val = userInput.value.trim();
    if (!val) return;

    // ui
    userInput.disabled = true;
    const btn = chatForm.querySelector("button");
    if (btn) btn.disabled = true;

    // append user message
    appendMessage({ role: "user", text: val, time: nowTime(), allowGrouping: true });

    // clear draft immediately
    localStorage.removeItem(DRAFT_KEY);
    userInput.value = "";

    // show typing
    const typing = showTyping();

    try {
      const resp = await fetch("/chat/ask/", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrftoken },
        body: JSON.stringify({ message: val })
      });

      if (!resp.ok) throw new Error("Network error");

      const data = await resp.json();
      removeEl(typing);

      let aiText = data.reply || data.message || data.text || "Sorry — couldn't generate a reply right now.";

      // append AI message (allow grouping)
      appendMessage({ role: "ai", text: aiText, time: nowTime(), allowGrouping: true });

    } catch (err) {
      console.error("chat error", err);
      removeEl(typing);
      appendMessage({ role: "ai", text: "⚠️ Unable to reach the server. Please try again later.", time: nowTime(), allowGrouping: false });
    } finally {
      userInput.disabled = false;
      if (btn) btn.disabled = false;
      userInput.focus();
    }
  });

  // Enter vs Shift+Enter
  userInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      chatForm.requestSubmit();
    }
  });

  // manage new-message hint on scroll
  chatBox.addEventListener("scroll", () => {
    if (isNearBottom()) newHint.style.display = "none";
  });

  // initial welcome if empty (only append one)
  if (!chatBox.querySelector(".message-group")) {
    appendMessage({ role: "ai", text: "👋 Welcome! Hello — I'm your AI companion here to listen and support you. How are you feeling today?", time: nowTime(), allowGrouping: false });
  } else {
    setTimeout(() => chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: "auto" }), 80);
  }

  // focus input
  userInput.focus();
});
