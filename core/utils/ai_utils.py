# core/ai_utils.py
import os
import random
import requests
from django.conf import settings
from huggingface_hub import InferenceClient

# --- API Configuration ---
HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HF_HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"} if HF_API_KEY else {}

# --- Models ---
SENTIMENT_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"

# --- Fallback responses ---
FALLBACK_RESPONSES = [
    "I’m here for you. You’re not alone in this, and it’s okay to reach out for help. 💙",
    "That sounds really tough. Remember to take things one step at a time — you’re doing your best. 🌼",
    "Your feelings matter. Let’s talk about what’s been troubling you. 🤍",
    "It’s okay to feel this way sometimes. You deserve care and kindness, especially from yourself. 💫",
]


# 🧩 Sentiment Analysis
def analyze_sentiment(text):
    """
    Uses Hugging Face sentiment model to detect distress level.
    Returns: distress_flag ('true' or 'false') and distress_level ('high', 'low', 'neutral')
    """
    try:
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{SENTIMENT_MODEL}",
            headers=HF_HEADERS,
            json={"inputs": text},
            timeout=20,
        )
        response.raise_for_status()
        result = response.json()[0][0]
        label = result["label"].lower()
        score = result["score"]

        if label == "negative" and score > 0.7:
            return {"distress_flag": "true", "distress_level": "high"}
        elif label == "negative":
            return {"distress_flag": "true", "distress_level": "medium"}
        else:
            return {"distress_flag": "false", "distress_level": "low"}

    except Exception as e:
        print("❌ Sentiment Model Error:", e)
        return {"distress_flag": "false", "distress_level": "unknown"}


# 🩵 Supportive Reply Generation
# def generate_supportive_reply(user_text):
#     """
#     Generates a short, empathetic supportive message using Hugging Face BlenderBot.
#     Falls back to local responses if API fails.
#     """
#     try:
#         response = requests.post(
#             f"https://api-inference.huggingface.co/models/{CHAT_MODEL}",
#             headers=HF_HEADERS,
#             json={"inputs": user_text},
#             timeout=25,
#         )
#         response.raise_for_status()
#         data = response.json()

#         if isinstance(data, list) and len(data) > 0 and "generated_text" in data[0]:
#             return data[0]["generated_text"].strip()
#         elif isinstance(data, dict) and "generated_text" in data:
#             return data["generated_text"].strip()
#         else:
#             return random.choice(FALLBACK_RESPONSES)

#     except Exception as e:
#         print("❌ Hugging Face API Error:", e)
#         return random.choice(FALLBACK_RESPONSES)

CHAT_MODEL = "NousResearch/Hermes-2-Pro-Llama-3-8B"
client = InferenceClient(token=HF_API_KEY)

def generate_supportive_reply(user_text):
    """
    Generates chat completions using the updated Hugging Face Hub client API.
    """
    try:
        completion = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "user", "content": user_text}
            ],
            max_tokens=150,
            temperature=0.8,
            top_p=0.9,
            # repetition_penalty=1.1,
        )
        reply = completion.choices[0].message["content"]
        return reply.strip() if reply else random.choice(FALLBACK_RESPONSES)

    except Exception as e:
        print("❌ HF Chat Model Error:", e)
        return random.choice(FALLBACK_RESPONSES)
