import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Moderation ---
def moderate_text(text):
    """Check if input violates OpenAI safety policies."""
    try:
        response = client.moderations.create(
            model="omni-moderation-latest",
            input=text
        )
        result = response.results[0]
        return result.flagged, result.categories, response
    except Exception as e:
        print("⚠️ Moderation Error:", e)
        return None, None, None

# --- Chatbot reply ---
def get_chat_reply(messages):
    """Get a supportive AI response with safety and error handling."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=150
        )
        reply = response.choices[0].message.content.strip()
        return reply, response
    except Exception as e:
        print("⚠️ Chat API Error:", e)
        return "I'm sorry, but I’m having trouble responding right now. Please try again in a bit.", None
