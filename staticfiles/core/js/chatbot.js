document.addEventListener("DOMContentLoaded", function () {
  const chatForm = document.getElementById("chat-form");
  const userInput = document.getElementById("user-input");
  const chatBox = document.getElementById("messages");

  chatForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    const message = userInput.value.trim();
    if (!message) return;

    // 🧍 Display user message
    appendMessage("You", message, "user");
    userInput.value = "";

    try {
      const response = await fetch("/chat/ask/", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: new URLSearchParams({ message }),
      });

      const data = await response.json();

      if (data.response) {
        appendMessage("AI", data.response, "ai");
      } else {
        appendMessage("AI", "⚠️ Something went wrong.", "error");
      }
    } catch (error) {
      console.error("Chat Error:", error);
      appendMessage("AI", "⚠️ Unable to connect to server.", "error");
    }

    // Always scroll to bottom
    chatBox.scrollTop = chatBox.scrollHeight;
  });

  // Helper function to add messages
  function appendMessage(sender, text, type) {
    const msgDiv = document.createElement("div");
    msgDiv.classList.add("message", type);
    msgDiv.innerHTML = `<strong>${sender}:</strong> ${text}`;
    chatBox.appendChild(msgDiv);
  }

  // Get CSRF token
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
});
