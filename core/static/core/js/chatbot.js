document.addEventListener("DOMContentLoaded", function () {
  const chatForm = document.getElementById("chat-form");
  const userInput = document.getElementById("user-input");
  const chatBox = document.getElementById("messages");

  // 🔐 Get CSRF token from cookies
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

  // 📤 Handle chat submission
  chatForm.addEventListener("submit", async function (e) {
    e.preventDefault();

    const message = userInput.value.trim();
    if (!message) return;

    // 🧍 Add user message bubble
    const userMsgDiv = document.createElement("div");
    userMsgDiv.classList.add("user-message");
    userMsgDiv.textContent = message;
    chatBox.appendChild(userMsgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
    userInput.value = "";

    // ⏳ Add temporary "AI is typing..." message
    const typingDiv = document.createElement("div");
    typingDiv.classList.add("ai-message");
    // typingDiv.textContent = "AI is thinking...";
    chatBox.appendChild(typingDiv);
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
      // 🤖 Send user message to backend
      const response = await fetch("/chat/ask/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify({ message: message }),
      });

      if (!response.ok) {
        throw new Error("Network response was not ok");
      }

      const data = await response.json();

      // Remove "AI is thinking..." message
      typingDiv.remove();

      // 💬 Create AI message bubble
      const aiMsgDiv = document.createElement("div");
      aiMsgDiv.classList.add("ai-message");
      aiMsgDiv.innerHTML = `
        <strong>AI:</strong> ${data.reply}
        ${
          data.emotion
            ? `<div class="emotion-tag">🧠 Emotion: <b>${data.emotion}</b> (${data.emotion_confidence})</div>`
            : ""
        }
        ${
          data.distress_detected
            ? `<div class="distress-alert">🚨 Distress detected (level: ${data.distress_level})</div>`
            : ""
        }
      `;
      chatBox.appendChild(aiMsgDiv);
      chatBox.scrollTop = chatBox.scrollHeight;
    } catch (error) {
      console.error("❌ Error:", error);

      // Remove typing bubble
      typingDiv.remove();

      // 🚨 Error message bubble
      const errorDiv = document.createElement("div");
      errorDiv.classList.add("ai-message", "text-danger");
      errorDiv.innerHTML = `<strong>AI:</strong> ⚠️ Unable to connect to the server. Please try again later.`;
      chatBox.appendChild(errorDiv);
      chatBox.scrollTop = chatBox.scrollHeight;
    }
  });
});
